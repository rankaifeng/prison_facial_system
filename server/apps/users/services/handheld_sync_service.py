"""
手持终端同步服务

通过 HTTP API 把 PrisonerArchive 罪犯数据同步到手持终端：
  1. 注册人员: POST http://{ip}:{port}/api/v2/person/create
  2. 注册照片: POST http://{ip}:{port}/face/create (服务端下载照片，base64上传)
  3. 设置识别回调: POST http://{ip}:{port}/setIdentifyCallBack

设备配置在 server/config/handheld_device.yml

并发控制说明：
  - trigger_sync() 原子完成"检查是否在跑 + 占位 + 启动线程"，杜绝双线程竞态
  - 每次 trigger 分配递增 run_id，Service 实例持有自己的 run_id，
    旧线程（含取消后仍在收尾的）写进度一律被丢弃，不会污染新一轮计数
"""
import base64
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import yaml
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.users.models import PrisonerArchive, HandheldSyncLog

logger = logging.getLogger(__name__)

BATCH_SIZE = 20  # 每批注册人员数
BATCH_INTERVAL_SEC = 0.5  # 批间隔
PHOTO_WORKERS = 3  # 照片注册并发线程数（手持终端性能弱，不宜过高）

_lock = threading.RLock()
_cancel_requested = False
_sync_thread_active = False
_sync_thread = None
_run_id = 0
_progress = {
    'run_id': 0,
    'is_running': False,
    'phase': 'idle',  # idle / persons / photos / callback / done / error
    'total': 0,
    'completed': 0,
    'success': 0,
    'fail': 0,
    'current_name': '',
    'message': '空闲',
    'started_at': None,
    'finished_at': None,
    'last_error': '',
    'persons_total': 0,
    'persons_success': 0,
    'persons_fail': 0,
    'photos_total': 0,
    'photos_completed': 0,
    'photos_success': 0,
    'photos_fail': 0,
    'photos_skipped': 0,
}


def _load_device_config():
    config_path = os.path.join(settings.BASE_DIR, 'config', 'handheld_device.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get('device', {})
    except Exception as e:
        logger.error('读取手持终端配置失败: %s', e)
        return {}


def get_sync_progress():
    with _lock:
        return dict(_progress)


def trigger_sync():
    """原子触发同步：检查+占位+启动线程在同一把锁内完成。

    已取消但旧线程还在收尾时，等待其退出后再启动新一轮（重试一次）。
    返回 (ok, msg)。
    """
    global _run_id, _sync_thread_active, _cancel_requested, _sync_thread
    with _lock:
        if _sync_thread_active and not _cancel_requested:
            return False, '已有同步任务在运行'

    # 已请求取消但旧线程未退出：等它收尾（照片/人员任务都会频繁检查取消标记，通常秒退）
    old = _sync_thread
    if old is not None and old.is_alive():
        old.join(timeout=5)

    with _lock:
        if _sync_thread_active:
            return False, '上一任务正在停止，请几秒后再试'
        _cancel_requested = False
        _run_id += 1
        run_id = _run_id
        _sync_thread_active = True
        _progress.update(
            run_id=run_id,
            is_running=True,
            phase='idle',
            message='准备同步...',
            started_at=timezone.now(),
            finished_at=None,
            last_error='',
        )
    thread = threading.Thread(target=HandheldSyncService(run_id).sync_all, daemon=True)
    with _lock:
        _sync_thread = thread
    thread.start()
    return True, '已触发同步'


def request_cancel():
    global _cancel_requested
    with _lock:
        _cancel_requested = True


def is_cancelled():
    with _lock:
        return _cancel_requested


def is_sync_thread_active():
    with _lock:
        return _sync_thread_active


def _update_progress(**kwargs):
    """仅供 controller/无 run_id 上下文使用（如取消时置状态）"""
    with _lock:
        _progress.update(kwargs)


def _get_photo_url(prisoner):
    """返回可下载的照片HTTP URL；无有效照片返回 None（调用方应跳过，绝不兜底外网测试图——内网无外网必然失败）"""
    from apps.users.controllers.archive_controller import _normalize_photo_url
    if not prisoner.media_info:
        return None
    for item in prisoner.media_info:
        xp = item.get('xp') if isinstance(item, dict) else None
        if xp:
            url = _normalize_photo_url(xp)
            if url.startswith('http://') or url.startswith('https://'):
                return url
    return None


def _sentence_end_to_timestamp(sentence_end):
    """刑期止日转13位时间戳，用于设备 expireTime"""
    if not sentence_end:
        return None
    for fmt in ('%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d'):
        try:
            dt = datetime.strptime(sentence_end, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    return None


def _get_new_prisoners():
    """获取完全新增的罪犯（档案库有但 HandheldSyncLog 没有记录的）"""
    all_prisoners = list(PrisonerArchive.objects.all())
    if not all_prisoners:
        return []

    synced = set(HandheldSyncLog.objects.values_list('prisoner_no', flat=True))
    return [p for p in all_prisoners if p.prisoner_no not in synced]


def _get_photo_pending_prisoners():
    """获取人员已注册但照片未同步的罪犯（上次照片失败的，或此前因无有效照片被跳过的）"""
    pending_nos = set(
        HandheldSyncLog.objects.filter(
            Q(person_synced=True, photo_synced=False) | Q(photo_skipped=True)
        )
        .values_list('prisoner_no', flat=True)
    )
    if not pending_nos:
        return []
    return list(PrisonerArchive.objects.filter(prisoner_no__in=pending_nos))


def _mark_person_synced(prisoner_nos):
    """标记人员已注册"""
    for no in prisoner_nos:
        HandheldSyncLog.objects.update_or_create(
            prisoner_no=no,
            defaults={'person_synced': True, 'synced_at': timezone.now()},
        )


def _mark_photo_synced(prisoner_nos):
    """标记照片已注册（同时清除跳过标记）"""
    for no in prisoner_nos:
        HandheldSyncLog.objects.update_or_create(
            prisoner_no=no,
            defaults={'photo_synced': True, 'photo_skipped': False, 'synced_at': timezone.now()},
        )


def _mark_photo_skipped(prisoner_nos):
    """标记照片被跳过（无有效照片URL）。photo_synced 置 True 避免当次重复计入，
    但 photo_skipped=True 使下次同步重新检查照片URL，档案照片补齐后自动补同步"""
    for no in prisoner_nos:
        HandheldSyncLog.objects.update_or_create(
            prisoner_no=no,
            defaults={'photo_synced': True, 'photo_skipped': True, 'synced_at': timezone.now()},
        )


class HandheldSyncService:
    """每个 run 一个实例，实例持有 run_id；进度写入必须匹配当前 run_id 才生效"""

    def __init__(self, run_id):
        self.run_id = run_id

    def _update(self, **kwargs):
        with _lock:
            if _run_id == self.run_id:
                _progress.update(kwargs)

    def sync_all(self):
        global _sync_thread_active
        try:
            self._do_sync()
        finally:
            with _lock:
                _sync_thread_active = False

    def _do_sync(self):
        cfg = _load_device_config()
        ip = cfg.get('ip', '')
        port = cfg.get('port', 8090)
        password = cfg.get('password', '')
        callback_url = cfg.get('callback_url', '')

        logger.info('[同步开始] 设备 %s:%s (run_id=%s)', ip, port, self.run_id)

        if not ip or ip == 'YOUR_DEVICE_IP':
            logger.error('[同步] 设备IP未配置')
            self._update(is_running=False, phase='error', message='设备IP未配置，请修改 config/handheld_device.yml',
                         finished_at=timezone.now(), last_error='设备IP未配置')
            return

        base_url = f'http://{ip}:{port}'
        self._update(is_running=True, phase='persons',
                     total=0, completed=0, success=0, fail=0,
                     persons_total=0, persons_success=0, persons_fail=0,
                     photos_total=0, photos_completed=0, photos_success=0,
                     photos_fail=0, photos_skipped=0,
                     message='检查新增罪犯...')

        try:
            # 增量：获取需要同步的罪犯
            new_prisoners = _get_new_prisoners()  # 完全新增（人员+照片都没注册）
            photo_pending = _get_photo_pending_prisoners()  # 人员已注册，照片失败需要重试

            if not new_prisoners and not photo_pending:
                logger.info('[同步] 没有新增罪犯，无需同步')
                self._update(is_running=False, phase='done',
                             message='没有新增罪犯，无需同步',
                             finished_at=timezone.now())
                return

            all_total = PrisonerArchive.objects.count()
            logger.info('[同步] 档案库共 %d 名罪犯，新增 %d 人，补照片 %d 人',
                        all_total, len(new_prisoners), len(photo_pending))

            # 步骤1: 批量注册人员（只处理完全新增的）
            ok_count, fail_count = 0, 0
            if new_prisoners:
                total_persons = len(new_prisoners)
                self._update(is_running=True, phase='persons', total=total_persons,
                             message=f'发现 {total_persons} 名新增罪犯，开始注册人员...')
                logger.info('[同步] === 步骤1: 注册人员（%d 人） ===', total_persons)
                ok_count, fail_count, _ = self._sync_persons(base_url, password, new_prisoners)
                if is_cancelled():
                    self._update(is_running=False, phase='done',
                                 message=f'同步已取消：人员注册 {ok_count}/{total_persons}',
                                 finished_at=timezone.now())
                    return
                logger.info('[同步] 人员注册完成：成功 %d，失败 %d', ok_count, fail_count)
                self._update(phase='persons', completed=ok_count + fail_count,
                             success=ok_count, fail=fail_count,
                             persons_total=total_persons, persons_success=ok_count,
                             persons_fail=fail_count,
                             message=f'人员注册完成：成功 {ok_count}，失败 {fail_count}')
            else:
                self._update(phase='persons', message='无新增人员注册', total=0, completed=0)

            # 步骤2: 注册照片（新增的 + 上次照片失败的）
            photo_prisoners = new_prisoners + photo_pending
            logger.info('[同步] === 步骤2: 注册照片（%d 人） ===', len(photo_prisoners))
            photo_count = sum(1 for p in photo_prisoners if _get_photo_url(p))
            self._update(phase='photos', message='开始注册照片...',
                         total=photo_count, completed=0, success=0, fail=0)
            photo_ok, photo_fail, photo_synced_nos, skipped = self._sync_photos(
                base_url, password, photo_prisoners)
            if is_cancelled():
                self._update(is_running=False, phase='done',
                             message=f'同步已取消：照片 {photo_ok}/{photo_count}',
                             finished_at=timezone.now())
                return
            logger.info('[同步] 照片注册完成：成功 %d，失败 %d，无照片跳过 %d',
                        photo_ok, photo_fail, skipped)
            self._update(success=photo_ok, fail=photo_fail,
                         photos_total=photo_count, photos_success=photo_ok,
                         photos_fail=photo_fail, photos_skipped=skipped,
                         message=(f'照片注册完成：成功 {photo_ok}，失败 {photo_fail}'
                                  + (f'，无照片跳过 {skipped}' if skipped else '')))

            # 步骤3: 设置识别回调
            cb_ok = False
            if callback_url and callback_url != 'http://YOUR_SERVER_IP:8000/api/v1/handheld-callback/':
                logger.info('[同步] === 步骤3: 设置识别回调 ===')
                self._update(phase='callback', message='设置识别回调...')
                cb_ok = self._set_callback(base_url, password, callback_url)
                logger.info('[同步] 回调设置%s', '成功' if cb_ok else '失败')
                self._update(message=f'回调设置{"成功" if cb_ok else "失败"}')

            new_count = len(new_prisoners)
            photo_total = len(photo_prisoners)
            logger.info('[同步] === 全部完成 === 新增 %d 人，人员 %d/%d，照片 %d/%d，跳过 %d，回调 %s',
                        new_count, ok_count, new_count, photo_ok, photo_total, skipped,
                        '成功' if cb_ok else '失败')
            msg_parts = []
            if new_count > 0:
                msg_parts.append(f'新增 {new_count} 人，人员注册 {ok_count}/{new_count}')
            if photo_pending:
                msg_parts.append(f'补照片 {len(photo_pending)} 人')
            msg_parts.append(f'照片注册 {photo_ok}/{photo_total}')
            if skipped:
                msg_parts.append(f'无照片跳过 {skipped}')
            msg_parts.append(f'回调设置{"成功" if cb_ok else "失败"}')
            self._update(is_running=False, phase='done',
                         message=f'同步完成：{"，".join(msg_parts)}',
                         finished_at=timezone.now())

        except Exception as e:
            logger.exception('[同步] 异常: %s', e)
            self._update(is_running=False, phase='error', message=f'同步异常: {e}',
                         finished_at=timezone.now(), last_error=str(e))

    def _register_person_payload(self, prisoner):
        person = {
            'id': prisoner.prisoner_no,
            'name': prisoner.prisoner_name or '',
            'idcardNum': prisoner.id_card or '',
        }
        expire_ts = _sentence_end_to_timestamp(prisoner.sentence_end)
        if expire_ts:
            person['expireTime'] = expire_ts
        return person

    def _register_person_single(self, base_url, password, prisoner):
        """单人注册，用于整批被拒后隔离问题人员"""
        person = self._register_person_payload(prisoner)
        try:
            resp = requests.post(
                f'{base_url}/api/v2/person/create',
                data={
                    'pass': password,
                    'persons': json.dumps([person], ensure_ascii=False),
                },
                timeout=30,
            )
            data = resp.json()
            if data.get('success'):
                logger.info('[人员注册] 单人 %s(%s) 成功', prisoner.prisoner_no, prisoner.prisoner_name)
                return True
            logger.warning('[人员注册] 单人 %s(%s) 被拒: %s',
                           prisoner.prisoner_no, prisoner.prisoner_name, data.get('msg', ''))
            return False
        except Exception as e:
            logger.warning('[人员注册] 单人 %s(%s) 异常: %s',
                           prisoner.prisoner_no, prisoner.prisoner_name, e)
            return False

    def _sync_persons(self, base_url, password, prisoners):
        ok = 0
        fail = 0
        synced_nos = []
        consecutive_conn_fail = 0
        MAX_CONSECUTIVE_FAIL = 5
        total = len(prisoners)
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info('[人员注册] 开始，共 %d 人，分 %d 批（每批%d人）', total, total_batches, BATCH_SIZE)

        for i in range(0, len(prisoners), BATCH_SIZE):
            if is_cancelled():
                logger.info('[人员注册] 被用户取消')
                break

            batch = prisoners[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            self._update(current_name=batch[0].prisoner_name if batch else '',
                         message=f'注册人员 {i + 1}-{min(i + BATCH_SIZE, total)} / {total}')
            logger.info('[人员注册] 批次 %d/%d，人数 %d', batch_num, total_batches, len(batch))

            # 连续连接失败视为设备服务不可用，剩余批次直接计失败并更新进度
            if consecutive_conn_fail >= MAX_CONSECUTIVE_FAIL:
                fail += len(batch)
                self._update(completed=ok + fail, success=ok, fail=fail)
                continue

            persons = [self._register_person_payload(p) for p in batch]
            batch_ok = False
            device_reachable = True
            for attempt in range(3):
                try:
                    logger.info('[人员注册] 批次 %d/%d 尝试 %d/3，请求 %s/api/v2/person/create',
                                batch_num, total_batches, attempt + 1, base_url)
                    resp = requests.post(
                        f'{base_url}/api/v2/person/create',
                        data={
                            'pass': password,
                            'persons': json.dumps(persons, ensure_ascii=False),
                        },
                        timeout=30,
                    )
                    logger.info('[人员注册] 批次 %d/%d 响应 HTTP %d: %s',
                                batch_num, total_batches, resp.status_code, resp.text.strip()[:200])
                    data = resp.json()
                    if data.get('success'):
                        ok += len(batch)
                        batch_ok = True
                        consecutive_conn_fail = 0
                        synced_nos.extend([p.prisoner_no for p in batch])
                        logger.info('[人员注册] 批次 %d/%d 成功（累计 %d/%d）', batch_num, total_batches, ok, total)
                        break
                    else:
                        logger.warning('[人员注册] 批次 %d/%d 失败 尝试%d/3: %s',
                                       batch_num, total_batches, attempt + 1, data.get('msg', ''))
                        if attempt < 2:
                            time.sleep(2)
                except requests.ConnectionError as e:
                    consecutive_conn_fail += 1
                    logger.warning('[人员注册] 批次 %d/%d 连接失败 尝试%d/3 (%d/%d连续失败): %s',
                                   batch_num, total_batches, attempt + 1, consecutive_conn_fail,
                                   MAX_CONSECUTIVE_FAIL, e)
                    if consecutive_conn_fail >= MAX_CONSECUTIVE_FAIL:
                        logger.error('[人员注册] 连续%d次连接失败，设备服务不可用', MAX_CONSECUTIVE_FAIL)
                        device_reachable = False
                        break
                    if attempt < 2:
                        time.sleep(2)
                except Exception as e:
                    logger.warning('[人员注册] 批次 %d/%d 异常 尝试%d/3: %s',
                                   batch_num, total_batches, attempt + 1, e)
                    if attempt < 2:
                        time.sleep(2)

            if not batch_ok:
                if device_reachable:
                    # 整批被设备拒绝（非连接问题）：逐个注册，隔离出问题人员，
                    # 避免 1 个人的脏数据把整批 20 人全部堵死
                    logger.warning('[人员注册] 批次 %d/%d 整批被拒，逐个注册隔离问题人员', batch_num, total_batches)
                    for p in batch:
                        if is_cancelled():
                            break
                        if self._register_person_single(base_url, password, p):
                            ok += 1
                            synced_nos.append(p.prisoner_no)
                        else:
                            fail += 1
                else:
                    fail += len(batch)

            self._update(completed=ok + fail, success=ok, fail=fail)
            time.sleep(BATCH_INTERVAL_SEC)

        # 标记已同步的人员
        if synced_nos:
            _mark_person_synced(synced_nos)
            logger.info('[人员注册] 已标记 %d 人为已注册', len(synced_nos))

        logger.info('[人员注册] 完成，成功 %d，失败 %d', ok, fail)
        return ok, fail, synced_nos

    def _sync_photos(self, base_url, password, prisoners):
        total = len(prisoners)
        logger.info('[照片注册] 开始，共 %d 人', total)

        # 准备任务列表（无有效照片的跳过并标记 photo_skipped，下次同步重新检查）
        tasks = []
        skipped_nos = []
        for idx, p in enumerate(prisoners):
            photo_url = _get_photo_url(p)
            if not photo_url:
                skipped_nos.append(p.prisoner_no)
                logger.warning('[照片注册] 跳过 %s(%s): 无有效照片URL', p.prisoner_no, p.prisoner_name)
                continue
            tasks.append((idx, p, photo_url))

        skip_count = len(skipped_nos)
        if skip_count > 0:
            _mark_photo_skipped(skipped_nos)
            logger.info('[照片注册] %d 人无有效照片，已跳过并标记，实际待注册 %d 人', skip_count, len(tasks))

        counter_lock = threading.Lock()
        results = {'ok': 0, 'fail': 0, 'done': 0}
        synced_nos = []

        def _download_photo(photo_url, prisoner_no):
            """下载照片转base64，重试一次"""
            for attempt in range(2):
                try:
                    img_resp = requests.get(photo_url, timeout=15)
                    img_resp.raise_for_status()
                    img_base64 = base64.b64encode(img_resp.content).decode('utf-8')
                    logger.info('[照片注册] %s 照片下载成功(尝试%d/2)，base64长度=%d',
                                prisoner_no, attempt + 1, len(img_base64))
                    return img_base64
                except Exception as e:
                    logger.warning('[照片注册] %s 照片下载失败 尝试%d/2: %s', prisoner_no, attempt + 1, e)
                    if attempt < 1:
                        time.sleep(1)
            return None

        def _post_face(p, img_base64):
            """调用设备 /face/create，返回 (ok, msg)"""
            try:
                resp = requests.post(
                    f'{base_url}/face/create',
                    data={
                        'pass': password,
                        'personId': p.prisoner_no,
                        'faceId': f'face_{p.prisoner_no}',
                        'imgBase64': img_base64,
                    },
                    timeout=30,
                )
                logger.info('[照片注册] %s 响应 HTTP %d: %s',
                            p.prisoner_no, resp.status_code, resp.text.strip()[:200])
                data = resp.json()
                if data.get('success'):
                    return True, ''
                return False, str(data.get('msg', ''))
            except requests.ConnectionError as e:
                logger.warning('[照片注册] %s 连接失败: %s', p.prisoner_no, e)
                return False, '连接失败'
            except Exception as e:
                logger.warning('[照片注册] %s 异常: %s', p.prisoner_no, e)
                return False, str(e)

        def _register_one(idx, p, photo_url):
            """单个照片注册：服务端下载照片转base64，发给设备"""
            if is_cancelled():
                return False

            self._update(current_name=p.prisoner_name or p.prisoner_no,
                         message=f'照片注册中: {p.prisoner_name or p.prisoner_no}')
            logger.info('[照片注册] %d/%d %s(%s) 下载照片...',
                        idx + 1, total, p.prisoner_name, p.prisoner_no)

            img_base64 = _download_photo(photo_url, p.prisoner_no)
            if not img_base64:
                return False

            ok, msg = _post_face(p, img_base64)
            if ok:
                logger.info('[照片注册] %s 成功', p.prisoner_no)
                return True

            # 设备报 person is null：设备端没有该人员档案（设备数据被清或
            # 批量注册被静默丢弃），自动补注册人员后重试一次照片注册
            if 'person is null' in msg.lower():
                logger.warning('[照片注册] %s 设备无此人员档案，自动补注册人员后重试', p.prisoner_no)
                if not self._register_person_single(base_url, password, p):
                    logger.warning('[照片注册] %s 补注册人员失败，放弃', p.prisoner_no)
                    return False
                ok, msg = _post_face(p, img_base64)
                if ok:
                    logger.info('[照片注册] %s 补注册后成功', p.prisoner_no)
                    return True

            logger.warning('[照片注册] %s 失败: %s', p.prisoner_no, msg)
            return False

        submitted = 0
        logger.info('[照片注册] 使用 %d 个并发线程', PHOTO_WORKERS)
        with ThreadPoolExecutor(max_workers=PHOTO_WORKERS) as executor:
            future_map = {}
            for idx, p, photo_url in tasks:
                if is_cancelled():
                    break
                future = executor.submit(_register_one, idx, p, photo_url)
                future_map[future] = (idx, p)
                submitted += 1
                # 每提交一个任务就更新进度，让前端能看到正在处理
                self._update(
                    current_name=p.prisoner_name or p.prisoner_no,
                    message=f'照片注册中 ({submitted}/{len(tasks)}): {p.prisoner_name or p.prisoner_no}'
                )
                time.sleep(0.2)  # 提交间隔，避免瞬间打满

            for future in as_completed(future_map):
                idx, p = future_map[future]
                with counter_lock:
                    results['done'] += 1
                    try:
                        if future.result():
                            results['ok'] += 1
                            synced_nos.append(p.prisoner_no)
                        else:
                            results['fail'] += 1
                    except Exception as e:
                        results['fail'] += 1
                        logger.error('[照片注册] %s 线程异常: %s', p.prisoner_no, e)

                    self._update(
                        completed=results['done'],
                        success=results['ok'],
                        fail=results['fail'],
                        photos_completed=results['done'],
                        photos_success=results['ok'],
                        photos_fail=results['fail'],
                        message=(f'照片注册 {results["done"]}/{len(tasks)}: '
                                 f'成功 {results["ok"]}，失败 {results["fail"]}')
                    )

        # 标记已同步的照片
        if synced_nos:
            _mark_photo_synced(synced_nos)
            logger.info('[照片注册] 已标记 %d 人为照片已注册', len(synced_nos))

        logger.info('[照片注册] 完成，成功 %d，失败 %d，跳过 %d',
                    results['ok'], results['fail'], skip_count)
        return results['ok'], results['fail'], synced_nos, skip_count

    def _set_callback(self, base_url, password, callback_url):
        try:
            logger.info('[回调设置] 请求 %s/setIdentifyCallBack，回调地址=%s', base_url, callback_url)
            resp = requests.post(
                f'{base_url}/setIdentifyCallBack',
                data={
                    'pass': password,
                    'callbackUrl': callback_url,
                },
                timeout=10,
            )
            logger.info('[回调设置] 响应 HTTP %d: %s', resp.status_code, resp.text.strip()[:200])
            data = resp.json()
            return data.get('success', False)
        except Exception as e:
            logger.warning('[回调设置] 失败: %s', e)
            return False
