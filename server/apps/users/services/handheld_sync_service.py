"""
手持终端同步服务

通过 HTTP API 把 PrisonerArchive 罪犯数据同步到手持终端：
  1. 注册人员: POST http://{ip}:{port}/api/v2/person/create
  2. 注册照片: POST http://{ip}:{port}/face/create (服务端下载照片，base64上传)
  3. 设置识别回调: POST http://{ip}:{port}/setIdentifyCallBack

设备配置在 server/config/handheld_device.yml
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
from django.utils import timezone

from apps.users.models import PrisonerArchive, HandheldSyncLog

logger = logging.getLogger(__name__)

BATCH_SIZE = 20  # 每批注册人员数
BATCH_INTERVAL_SEC = 0.5  # 批间隔

_lock = threading.Lock()
_cancel_requested = False
_sync_thread_active = False
_progress = {
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


def request_cancel():
    global _cancel_requested
    with _lock:
        _cancel_requested = True


def is_cancelled():
    with _lock:
        return _cancel_requested


def _reset_cancel():
    global _cancel_requested
    with _lock:
        _cancel_requested = False


def is_sync_thread_active():
    with _lock:
        return _sync_thread_active


def _update_progress(**kwargs):
    with _lock:
        _progress.update(kwargs)


def _get_photo_url(prisoner):
    from apps.users.controllers.archive_controller import _normalize_photo_url
    if not prisoner.media_info:
        return None
    for item in prisoner.media_info:
        xp = item.get('xp') if isinstance(item, dict) else None
        if xp:
            url = _normalize_photo_url(xp)
            if url.startswith('http://') or url.startswith('https://'):
                return url
    # xp 是 Windows 路径（非内网环境），用测试图片
    return 'https://imagepphcloud.thepaper.cn/pph/image/95/868/3.jpg'


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
    """获取人员已注册但照片未同步的罪犯（上次照片失败的）"""
    pending_nos = set(
        HandheldSyncLog.objects.filter(person_synced=True, photo_synced=False)
        .values_list('prisoner_no', flat=True)
    )
    if not pending_nos:
        return []
    return list(PrisonerArchive.objects.filter(prisoner_no__in=pending_nos))


def _mark_person_synced(prisoner_nos):
    """标记人员已注册"""
    for no in prisoner_nos:
        obj, created = HandheldSyncLog.objects.get_or_create(prisoner_no=no)
        obj.person_synced = True
        obj.save(update_fields=['person_synced', 'synced_at'])


def _mark_photo_synced(prisoner_nos):
    """标记照片已注册"""
    for no in prisoner_nos:
        obj, created = HandheldSyncLog.objects.get_or_create(prisoner_no=no)
        obj.photo_synced = True
        obj.save(update_fields=['photo_synced', 'synced_at'])


class HandheldSyncService:

    def sync_all(self):
        global _sync_thread_active
        _reset_cancel()
        with _lock:
            _sync_thread_active = True
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

        logger.info('[同步开始] 设备 %s:%s', ip, port)

        if not ip or ip == 'YOUR_DEVICE_IP':
            logger.error('[同步] 设备IP未配置')
            _update_progress(is_running=False, phase='error', message='设备IP未配置，请修改 config/handheld_device.yml',
                             finished_at=timezone.now(), last_error='设备IP未配置')
            return

        base_url = f'http://{ip}:{port}'
        _update_progress(is_running=True, phase='persons', message='检查新增罪犯...', started_at=timezone.now(),
                         finished_at=None, last_error='', total=0, completed=0, success=0, fail=0,
                         persons_total=0, persons_success=0, persons_fail=0,
                         photos_total=0, photos_completed=0, photos_success=0, photos_fail=0)

        try:
            # 增量：获取需要同步的罪犯
            new_prisoners = _get_new_prisoners()  # 完全新增（人员+照片都没注册）
            photo_pending = _get_photo_pending_prisoners()  # 人员已注册，照片失败需要重试

            if not new_prisoners and not photo_pending:
                logger.info('[同步] 没有新增罪犯，无需同步')
                _update_progress(is_running=False, phase='done',
                                 message='没有新增罪犯，无需同步',
                                 finished_at=timezone.now())
                return

            all_total = PrisonerArchive.objects.count()
            logger.info('[同步] 档案库共 %d 名罪犯，新增 %d 人，补照片 %d 人', all_total, len(new_prisoners), len(photo_pending))

            # 步骤1: 批量注册人员（只处理完全新增的）
            ok_count, fail_count, synced_nos = 0, 0, []
            if new_prisoners:
                total_persons = len(new_prisoners)
                _update_progress(is_running=True, phase='persons', total=total_persons,
                                 message=f'发现 {total_persons} 名新增罪犯，开始注册人员...')
                logger.info('[同步] === 步骤1: 注册人员（%d 人） ===', total_persons)
                ok_count, fail_count, synced_nos = self._sync_persons(base_url, password, new_prisoners)
                if is_cancelled():
                    _update_progress(is_running=False, phase='done',
                                     message=f'同步已取消：人员注册 {ok_count}/{total_persons}',
                                     finished_at=timezone.now())
                    return
                logger.info('[同步] 人员注册完成：成功 %d，失败 %d', ok_count, fail_count)
                _update_progress(phase='persons', completed=ok_count + fail_count, success=ok_count, fail=fail_count,
                                 persons_total=total_persons, persons_success=ok_count, persons_fail=fail_count,
                                 message=f'人员注册完成：成功 {ok_count}，失败 {fail_count}')
            else:
                _update_progress(phase='persons', message='无新增人员注册', total=0, completed=0)

            # 步骤2: 注册照片（新增的 + 上次照片失败的）
            photo_prisoners = new_prisoners + photo_pending
            logger.info('[同步] === 步骤2: 注册照片（%d 人） ===', len(photo_prisoners))
            photo_count = sum(1 for p in photo_prisoners if _get_photo_url(p))
            _update_progress(phase='photos', message='开始注册照片...',
                             total=photo_count, completed=0, success=0, fail=0)
            photo_ok, photo_fail, photo_synced_nos = self._sync_photos(base_url, password, photo_prisoners)
            if is_cancelled():
                _update_progress(is_running=False, phase='done',
                                 message=f'同步已取消：照片 {photo_ok}/{photo_count}',
                                 finished_at=timezone.now())
                return
            logger.info('[同步] 照片注册完成：成功 %d，失败 %d', photo_ok, photo_fail)
            _update_progress(success=photo_ok, fail=photo_fail,
                             photos_total=photo_count, photos_success=photo_ok, photos_fail=photo_fail,
                             message=f'照片注册完成：成功 {photo_ok}，失败 {photo_fail}')

            # 步骤3: 设置识别回调
            cb_ok = False
            if callback_url and callback_url != 'http://YOUR_SERVER_IP:8000/api/v1/handheld-callback/':
                logger.info('[同步] === 步骤3: 设置识别回调 ===')
                _update_progress(phase='callback', message='设置识别回调...')
                cb_ok = self._set_callback(base_url, password, callback_url)
                logger.info('[同步] 回调设置%s', '成功' if cb_ok else '失败')
                _update_progress(message=f'回调设置{"成功" if cb_ok else "失败"}')

            new_count = len(new_prisoners)
            photo_total = len(photo_prisoners)
            logger.info('[同步] === 全部完成 === 新增 %d 人，人员 %d/%d，照片 %d/%d，回调 %s',
                        new_count, ok_count, new_count, photo_ok, photo_total, '成功' if cb_ok else '失败')
            msg_parts = []
            if new_count > 0:
                msg_parts.append(f'新增 {new_count} 人，人员注册 {ok_count}/{new_count}')
            if photo_pending:
                msg_parts.append(f'补照片 {len(photo_pending)} 人')
            msg_parts.append(f'照片注册 {photo_ok}/{photo_total}')
            msg_parts.append(f'回调设置{"成功" if cb_ok else "失败"}')
            _update_progress(is_running=False, phase='done',
                             message=f'同步完成：{"，".join(msg_parts)}',
                             finished_at=timezone.now())

        except Exception as e:
            logger.exception('[同步] 异常: %s', e)
            _update_progress(is_running=False, phase='error', message=f'同步异常: {e}',
                             finished_at=timezone.now(), last_error=str(e))

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
            if consecutive_conn_fail >= MAX_CONSECUTIVE_FAIL:
                fail += len(prisoners[i:i + BATCH_SIZE])
                continue

            batch = prisoners[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            persons = []
            for p in batch:
                person = {
                    'id': p.prisoner_no,
                    'name': p.prisoner_name or '',
                    'idcardNum': p.id_card or '',
                }
                expire_ts = _sentence_end_to_timestamp(p.sentence_end)
                if expire_ts:
                    person['expireTime'] = expire_ts
                persons.append(person)

            _update_progress(current_name=batch[0].prisoner_name if batch else '',
                             message=f'注册人员 {i + 1}-{min(i + BATCH_SIZE, total)} / {total}')
            logger.info('[人员注册] 批次 %d/%d，人数 %d', batch_num, total_batches, len(batch))

            batch_ok = False
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
                                   batch_num, total_batches, attempt + 1, consecutive_conn_fail, MAX_CONSECUTIVE_FAIL, e)
                    if consecutive_conn_fail >= MAX_CONSECUTIVE_FAIL:
                        logger.error('[人员注册] 连续%d次连接失败，设备服务不可用', MAX_CONSECUTIVE_FAIL)
                        break
                    if attempt < 2:
                        time.sleep(2)
                except Exception as e:
                    logger.warning('[人员注册] 批次 %d/%d 异常 尝试%d/3: %s',
                                   batch_num, total_batches, attempt + 1, e)
                    if attempt < 2:
                        time.sleep(2)

            if not batch_ok:
                fail += len(batch)

            _update_progress(completed=ok + fail, success=ok, fail=fail)
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

        # 准备任务列表（过滤无照片的）
        tasks = []
        skip_count = 0
        for idx, p in enumerate(prisoners):
            photo_url = _get_photo_url(p)
            if not photo_url:
                skip_count += 1
                logger.warning('[照片注册] 跳过 %s(%s): 无照片URL', p.prisoner_no, p.prisoner_name)
                continue
            tasks.append((idx, p, photo_url))

        if skip_count > 0:
            logger.info('[照片注册] 跳过无照片 %d 人，实际待注册 %d 人', skip_count, len(tasks))

        counter_lock = threading.Lock()
        results = {'ok': 0, 'fail': skip_count, 'done': 0, 'cancelled': False}
        synced_nos = []

        def _register_one(idx, p, photo_url):
            """单个照片注册：服务端下载照片转base64，发给设备（不重试）"""
            if is_cancelled() or results['cancelled']:
                return False

            _update_progress(current_name=p.prisoner_name or p.prisoner_no,
                             message=f'照片注册中: {p.prisoner_name or p.prisoner_no}')
            logger.info('[照片注册] %d/%d %s(%s) 下载照片...', idx + 1, total, p.prisoner_name, p.prisoner_no)

            # 服务端下载照片转base64
            try:
                img_resp = requests.get(photo_url, timeout=15)
                img_resp.raise_for_status()
                img_base64 = base64.b64encode(img_resp.content).decode('utf-8')
                logger.info('[照片注册] %s 照片下载成功，base64长度=%d', p.prisoner_no, len(img_base64))
            except Exception as e:
                logger.warning('[照片注册] %s 照片下载失败: %s', p.prisoner_no, e)
                return False

            # 发送base64到设备
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
                    logger.info('[照片注册] %s 成功', p.prisoner_no)
                    return True
                else:
                    logger.warning('[照片注册] %s 失败: %s', p.prisoner_no, data.get('msg', ''))
                    return False
            except requests.ConnectionError as e:
                logger.warning('[照片注册] %s 连接失败: %s', p.prisoner_no, e)
                return False
            except Exception as e:
                logger.warning('[照片注册] %s 异常: %s', p.prisoner_no, e)
                return False

        WORKERS = 5  # 并发线程数
        submitted = 0

        logger.info('[照片注册] 使用 %d 个并发线程', WORKERS)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            future_map = {}
            for idx, p, photo_url in tasks:
                if is_cancelled():
                    results['cancelled'] = True
                    break
                future = executor.submit(_register_one, idx, p, photo_url)
                future_map[future] = (idx, p)
                submitted += 1
                # 每提交一个任务就更新进度，让前端能看到正在处理
                _update_progress(
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

                    _update_progress(
                        completed=results['done'] + skip_count,
                        success=results['ok'],
                        fail=results['fail'],
                        photos_completed=results['done'],
                        photos_success=results['ok'],
                        photos_fail=results['fail'],
                        message=f'照片注册 {results["done"]}/{len(tasks)}: 成功 {results["ok"]}，失败 {results["fail"]}'
                    )

        # 标记已同步的照片
        if synced_nos:
            _mark_photo_synced(synced_nos)
            logger.info('[照片注册] 已标记 %d 人为照片已注册', len(synced_nos))

        logger.info('[照片注册] 完成，成功 %d，失败 %d', results['ok'], results['fail'])
        return results['ok'], results['fail'], synced_nos

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
