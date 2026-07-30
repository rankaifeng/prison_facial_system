"""
Celery 定时任务
"""
import logging
from datetime import date, timedelta
from celery import shared_task
from apps.users.models import DailyStatistics, HistoryStatistics, TodayExitRecord

logger = logging.getLogger(__name__)

HISTORY_REASON_FIELDS = [
    ('刑满释放', 'exit_reason_1'),
    ('外出就医', 'exit_reason_2'),
    ('外出教育', 'exit_reason_3'),
    ('离监探亲', 'exit_reason_4'),
    ('押回重审', 'exit_reason_5'),
]


def _build_history_reason_counts(reason_stats):
    reason_stats = reason_stats or {}
    return {field: reason_stats.get(reason, 0) for reason, field in HISTORY_REASON_FIELDS}


@shared_task
def generate_exit_video(record_id):
    """
    异步生成出监/回监记录的录像
    """
    from apps.users.models import ExitEntryRecord
    from apps.users.controllers.video_controller import (
        _build_rtsp_urls, _calc_duration_seconds,
        _get_video_cache_path, _video_exists_cached, VIDEOS_ROOT,
        load_cameras_config,
    )
    from apps.users.rtsp_to_mp4 import record_rtsp_to_mp4

    try:
        record = ExitEntryRecord.objects.get(id=record_id)
    except ExitEntryRecord.DoesNotExist:
        logger.error(f"记录不存在: id={record_id}")
        return f"记录不存在: {record_id}"

    # 检查是否已经有视频
    if record.video_url:
        logger.info(f"记录 {record_id} 已有视频: {record.video_url}")
        return f"已有视频: {record.video_url}"

    # 检查是否有时间范围
    if not record.start_time or not record.end_time:
        logger.info(f"记录 {record_id} 没有时间范围，跳过视频生成")
        return f"没有时间范围"

    # 从配置获取摄像头信息
    config = load_cameras_config()
    cameras = config.get('cameras', [])

    # 入监/回监用回监摄像头(1)，出监用出监摄像头(0)
    camera_index = 1 if record.type == 'entry' else 0
    if camera_index >= len(cameras):
        logger.error(f"摄像头索引 {camera_index} 不存在")
        return f"摄像头不存在"

    camera = cameras[camera_index]
    if not camera.get('enabled'):
        logger.error(f"摄像头未启用: {camera_index}")
        return f"摄像头未启用"

    rtsp_base = camera.get('rtsp_url', '')
    if not rtsp_base:
        logger.error(f"摄像头RTSP地址未配置")
        return f"RTSP地址未配置"

    # 计算录像时长
    duration = _calc_duration_seconds(record.start_time, record.end_time)
    logger.info(f"记录 {record_id} 开始生成视频, 时长: {duration}秒")

    # 检查是否已有缓存
    cached_path = _video_exists_cached(record.start_time, record.end_time, camera_index, record_id)
    if cached_path:
        video_url = f"/media/videos/{cached_path.name}"
        record.video_url = video_url
        record.save(update_fields=['video_url'])
        logger.info(f"记录 {record_id} 使用缓存视频: {video_url}")
        return f"使用缓存: {video_url}"

    # 生成视频文件路径
    video_path = _get_video_cache_path(record.start_time, record.end_time, camera_index, record_id)
    video_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建 RTSP URL（紧凑格式优先）
    rtsp_urls = _build_rtsp_urls(rtsp_base, record.start_time, record.end_time)
    max_wait = duration + 30

    last_error = None
    for i, rtsp_url in enumerate(rtsp_urls):
        print(f"[Video] 尝试URL {i+1}: {rtsp_url}")
        result = record_rtsp_to_mp4(
            rtsp_url=rtsp_url,
            output_path=str(video_path),
            duration=duration,
            timeout=max_wait,
            stall_timeout=60,
            overwrite=True,
            pre_probe=True,
            verbose=True,
        )

        if result["success"]:
            video_url = f"/media/videos/{video_path.name}"
            record.video_url = video_url
            record.save(update_fields=['video_url'])
            logger.info(f"记录 {record_id} 视频生成成功: {video_url}")
            return f"成功: {video_url}"

        last_error = result["message"]
        logger.warning(f"记录 {record_id} URL {i+1} 失败: {last_error}")

    logger.error(f"记录 {record_id} 视频生成全部失败: {last_error}")
    return f"失败: {last_error}"


@shared_task
def reset_daily_stats():
    """
    每天凌晨执行：同步昨日数据到历史记录，并重置当日统计
    """
    # 清空今日出监记录表
    deleted_count, _ = TodayExitRecord.objects.all().delete()
    logger.info(f'已清空今日出监记录: {deleted_count} 条')

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 获取昨日的统计数据
    daily_stats = DailyStatistics.objects.filter(date=yesterday)

    if not daily_stats.exists():
        logger.info(f'昨日({yesterday})没有统计数据，跳过同步')
        return '昨日无统计数据'

    synced_count = 0
    reset_count = 0

    for stat in daily_stats:
        # 同步到历史记录
        HistoryStatistics.objects.create(
            prison_area=stat.prison_area,
            prison_area_name=stat.prison_area_name,
            date=yesterday,
            exit_count=stat.exit_count,
            **_build_history_reason_counts(stat.reason_stats),
            entry_count=stat.entry_count,
        )
        synced_count += 1

        DailyStatistics.objects.get_or_create(
            prison_area=stat.prison_area,
            date=today,
            defaults={
                'prison_area_name': stat.prison_area_name,
                'exit_count': 0,
                'entry_count': 0,
                'in_prison_count': stat.in_prison_count,
                'work_count': 0,
                'reason_stats': {},
            }
        )
        reset_count += 1

    message = f'完成: {yesterday}数据已同步({synced_count}条)，{today}统计已重置({reset_count}条)'
    logger.info(message)
    return message


@shared_task
def sync_prisoner_data_task():
    """每天凌晨自动同步罪犯档案数据"""
    from django.core.management import call_command
    try:
        logger.info('开始自动同步罪犯数据...')
        call_command('sync_prisoner_data', '--real-api', '--dahua')
        logger.info('罪犯数据同步完成')
        return '罪犯数据同步完成'
    except Exception as e:
        logger.error(f'罪犯数据同步失败: {e}')
        return f'同步失败: {e}'


def _sync_to_dahua_direct(report_fn=None):
    """
    直接同步到大华门禁系统（从数据库读取，不重新同步数据）
    返回: (success_count, fail_count, skip_count, message)
    """
    import os
    import requests
    import base64
    import yaml
    from django.conf import settings
    from apps.users.models import PrisonerArchive

    def log(msg):
        logger.info(f'[大华同步] {msg}')
        if report_fn:
            report_fn(msg)

    # 1. 加载大华配置
    config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        msg = f'加载 cameras.yml 失败: {e}'
        logger.error(f'[大华同步] {msg}')
        return 0, 0, 0, msg

    dahua_config = config.get('dahua', {})
    base_url = dahua_config.get('base_url', '')
    if not base_url:
        msg = '大华平台 base_url 未配置'
        logger.error(f'[大华同步] {msg}')
        return 0, 0, 0, msg

    username = dahua_config.get('userName', '')
    password = dahua_config.get('password', '')
    auth = requests.auth.HTTPDigestAuth(username, password) if username else None

    log(f'大华平台地址: {base_url}')

    # 2. 验证连通性
    log('正在测试大华平台连接...')
    try:
        url = f"{base_url}/cgi-bin/magicBox.cgi?action=getDeviceType"
        resp = requests.get(url, auth=auth, timeout=(5, 10))
        log(f'大华平台连接测试: status={resp.status_code}, response={resp.text[:100]}')
        if resp.status_code != 200:
            msg = f'大华平台连接失败, status={resp.status_code}'
            logger.error(f'[大华同步] {msg}')
            return 0, 0, 0, msg
    except requests.RequestException as e:
        msg = f'大华平台连接异常: {e}'
        logger.error(f'[大华同步] {msg}')
        return 0, 0, 0, msg

    # 3. 获取档案数据（增量同步，不清空设备）
    log('正在读取档案数据...')
    archives = PrisonerArchive.objects.all()
    prisoners = list(archives.values('prisoner_no', 'prisoner_name', 'id_card', 'media_info', 'last_synced_photo_url'))
    if not prisoners:
        msg = '档案库无数据，跳过大华同步'
        log(msg)
        return 0, 0, 0, msg

    log(f'总人数: {len(prisoners)}')

    # 5. 先插入用户到大华（不管照片能不能下载）
    user_url = f"{base_url}/cgi-bin/AccessUser.cgi?action=insertMulti"
    users = []
    for p in prisoners:
        users.append({
            'UserID': p['prisoner_no'],
            'UserName': p['prisoner_name'],
            'UserType': 0,
            'UseTime': 1,
            'IsFirstEnter': True,
            'FirstEnterDoors': [0],
            'UserStatus': 0,
            'Authority': 2,
            'CitizenIDNo': p.get('id_card', ''),
            'Password': '123456',
            'Doors': [0],
            'ValidFrom': '2026-01-01 00:00:00',
            'ValidTo': '2099-12-31 23:59:59',
        })

    import time
    user_success = 0
    user_fail = 0
    batch_size = 10
    total_batches = (len(users) + batch_size - 1) // batch_size
    log(f'开始同步用户信息，共 {total_batches} 批...')
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        batch_num = i // batch_size + 1
        try:
            payload = {'UserList': batch}
            resp = requests.post(user_url, json=payload, auth=auth, timeout=(5, 30))
            text = resp.text.strip()
            if 'ok' in text.lower():
                user_success += len(batch)
                log(f'用户批次 {batch_num}/{total_batches}: 插入 {len(batch)} 个 (累计 {user_success}/{len(users)})')
            else:
                user_fail += len(batch)
                log(f'用户批次 {batch_num}/{total_batches} 失败: {text[:200]}')
        except requests.ConnectionError as e:
            user_fail += len(batch)
            log(f'用户批次 {batch_num}/{total_batches} 连接失败: {e}')
        except requests.Timeout as e:
            user_fail += len(batch)
            log(f'用户批次 {batch_num}/{total_batches} 超时: {e}')
        except requests.RequestException as e:
            user_fail += len(batch)
            log(f'用户批次 {batch_num}/{total_batches} 请求异常: {e}')
        time.sleep(2)

    # 5. 构建照片URL映射
    def fix_photo_url(url):
        if not url:
            return url
        url = url.replace('http://10.2.48.86/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.48.86:80/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.48.86:8080/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.50.16:8080/', 'http://10.2.50.16/')
        return url

    photo_map = {}
    no_photo = 0
    need_sync = []  # [(prisoner_no, photo_url), ...]
    for p in prisoners:
        media = p.get('media_info') or []
        current_url = ''
        for m in media:
            xp = fix_photo_url(m.get('xp', ''))
            if xp:
                current_url = xp
                photo_map[p['prisoner_no']] = xp
                break
        if not current_url:
            no_photo += 1
            continue
        need_sync.append((p['prisoner_no'], current_url))

    log(f'有照片: {len(need_sync)} 人, 无照片: {no_photo} 人')

    # 6. 插入人脸照片到大华（insertMulti 批量，每批最多10张，照片压缩到100KB以下）
    face_url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertMulti"

    def compress_photo(photo_bytes, max_size=50 * 1024):
        """压缩照片，目标50KB（base64后约67KB，留足够余量）"""
        from io import BytesIO
        from PIL import Image
        img = Image.open(BytesIO(photo_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        for quality in (70, 55, 40, 30, 20, 15, 10):
            buf = BytesIO()
            img.save(buf, format='JPEG', quality=quality)
            if buf.tell() <= max_size:
                return buf.getvalue()
        w, h = img.size
        for scale in (0.75, 0.5, 0.35, 0.25):
            resized = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            for quality in (50, 35, 20, 10):
                buf = BytesIO()
                resized.save(buf, format='JPEG', quality=quality)
                if buf.tell() <= max_size:
                    return buf.getvalue()
        return buf.getvalue()

    def download_photo_bytes(photo_url):
        try:
            r = requests.get(photo_url, timeout=15)
            r.raise_for_status()
            content = r.content
            if len(content) < 100:
                log(f'照片文件过小({len(content)}B): {photo_url}')
                return None
            return content
        except requests.Timeout:
            log(f'下载照片超时: {photo_url}')
            return None
        except requests.ConnectionError:
            log(f'下载照片连接失败: {photo_url}')
            return None
        except requests.HTTPError as e:
            log(f'下载照片HTTP错误({e.response.status_code}): {photo_url}')
            return None
        except Exception as e:
            log(f'下载照片异常: {photo_url} -> {e}')
            return None

    face_success = 0
    face_fail = 0
    download_fail = 0
    total = len(need_sync)

    if not need_sync:
        log('无可同步照片')
    else:
        log(f'开始同步人脸照片，共 {total} 人...')

        # 下载并压缩需要同步的照片
        ready_list = []  # [(prisoner_no, photo_b64, photo_url), ...]
        download_count = 0
        for prisoner_no, photo_url in need_sync:
            download_count += 1
            photo_bytes = download_photo_bytes(photo_url)
            if not photo_bytes:
                download_fail += 1
                continue
            compressed = compress_photo(photo_bytes)
            photo_b64 = base64.b64encode(compressed).decode('utf-8')
            ready_list.append((prisoner_no, photo_b64, photo_url))
            if download_count % 50 == 0:
                log(f'下载进度: {download_count}/{total} (成功 {len(ready_list)}, 失败 {download_fail})')

        log(f'准备就绪: {len(ready_list)} 人, 下载失败: {download_fail} 人')

        # 逐张验证大小，过滤掉仍然过大的
        import json as json_mod
        final_list = []
        for prisoner_no, photo_b64, photo_url in ready_list:
            b64_size = len(photo_b64)
            if b64_size > 100 * 1024:  # base64超过100KB的跳过
                log(f'跳过 {prisoner_no}: 照片base64过大({b64_size // 1024}KB)')
                continue
            final_list.append((prisoner_no, photo_b64, photo_url))

        log(f'验证通过: {len(final_list)} 人, 被过滤: {len(ready_list) - len(final_list)} 人')

        # 诊断: 测试第一张照片
        if final_list:
            test_pid, test_b64, _ = final_list[0]
            log(f'诊断: 测试用户 {test_pid}, base64大小 {len(test_b64)} bytes')
            test_payload = {'FaceList': [{'UserID': test_pid, 'PhotoData': [test_b64], 'PhotoURL': []}]}
            log(f'诊断: insertMulti 请求体 {len(json_mod.dumps(test_payload))} bytes')
            try:
                r = requests.post(face_url, json=test_payload, auth=auth, timeout=(5, 30))
                log(f'诊断: insertMulti 响应 [HTTP {r.status_code}] {repr(r.text)}')
            except Exception as e:
                log(f'诊断: insertMulti 异常 {e}')
            # 测试 insertSingle
            single_url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertSingle"
            try:
                r = requests.post(single_url, json={'UserID': test_pid, 'PhotoData': [test_b64], 'PhotoURL': []}, auth=auth, timeout=(5, 30))
                log(f'诊断: insertSingle 响应 [HTTP {r.status_code}] {repr(r.text)}')
            except Exception as e:
                log(f'诊断: insertSingle 异常 {e}')

        def _send_single(pid, b64_data):
            """发送单个人脸，返回 (ok, error_msg)"""
            single_payload = {'FaceList': [{'UserID': pid, 'PhotoData': [b64_data], 'PhotoURL': []}]}
            try:
                r = requests.post(face_url, json=single_payload, auth=auth, timeout=(5, 60))
                if 'ok' in r.text.strip().lower():
                    return True, None
                return False, f'[HTTP {r.status_code}] {r.text.strip()}'
            except Exception as e:
                return False, str(e)

        # 批量发送，每批10张
        batch_size = 10
        total_batches = (len(final_list) + batch_size - 1) // batch_size if final_list else 0
        for i in range(0, len(final_list), batch_size):
            batch = final_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            face_list = [{'UserID': pid, 'PhotoData': [b64], 'PhotoURL': []} for pid, b64, _ in batch]
            payload = {'FaceList': face_list}
            payload_size = len(json_mod.dumps(payload))
            batch_ok = False

            for attempt in range(3):
                try:
                    resp = requests.post(face_url, json=payload, auth=auth, timeout=(5, 120))
                    text = resp.text.strip().lower()
                    if 'ok' in text:
                        for prisoner_no, _, photo_url in batch:
                            PrisonerArchive.objects.filter(prisoner_no=prisoner_no).update(last_synced_photo_url=photo_url)
                        face_success += len(batch)
                        log(f'人脸批次 {batch_num}/{total_batches}: 成功 {len(batch)} 个 (累计 {face_success}/{len(final_list)})')
                        batch_ok = True
                        break
                    else:
                        log(f'人脸批次 {batch_num}/{total_batches} 尝试{attempt+1}/3 失败: [HTTP {resp.status_code}] {resp.text.strip()} (请求体 {payload_size // 1024}KB)')
                        if attempt < 2:
                            time.sleep(3)
                except requests.RequestException as e:
                    log(f'人脸批次 {batch_num}/{total_batches} 尝试{attempt+1}/3 异常: {e}')
                    if attempt < 2:
                        time.sleep(3)

            if not batch_ok:
                log(f'人脸批次 {batch_num}/{total_batches} 批量失败，逐个发送排查...')
                batch_success = 0
                batch_fail = 0
                for pid, b64_data, photo_url in batch:
                    ok, err = _send_single(pid, b64_data)
                    if ok:
                        PrisonerArchive.objects.filter(prisoner_no=pid).update(last_synced_photo_url=photo_url)
                        batch_success += 1
                    else:
                        batch_fail += 1
                        log(f'  用户 {pid} 失败: {err} (base64 {len(b64_data) // 1024}KB)')
                    time.sleep(0.5)
                face_success += batch_success
                face_fail += batch_fail
                log(f'人脸批次 {batch_num}/{total_batches} 逐个结果: 成功 {batch_success}, 失败 {batch_fail}')
            time.sleep(1)

    # 7. 汇总
    msg = (f'大华同步完成: 用户成功 {user_success}/{len(prisoners)}, '
           f'人脸成功 {face_success}/{total}, 下载失败 {download_fail}')
    log(msg)

    return face_success, face_fail, 0, msg


@shared_task(bind=True)
def sync_prisoner_data_with_progress(self):
    """手动同步罪犯数据（带进度报告）"""
    import os, requests, re, time
    from xml.etree import ElementTree as ET
    from django.conf import settings
    from apps.users.models import PrisonerArchive

    API_BASE = os.getenv('RTI_API_BASE', 'http://10.2.50.16:4092')
    PHOTO_BASE_URL = os.getenv('PHOTO_BASE_URL', '').rstrip('/')
    GET_IDS_URL = f"{API_BASE}/rti/service/invoke/arg0/unitop/arg1/unitop/arg2/zf_zyljbh/arg3/@zy='zy'"
    POST_URL = f'{API_BASE}/rti/service'

    def report(step, current, total, message):
        percent = int(current / total * 100) if total > 0 else 0
        logger.info(f'[同步进度] {step}: {message} ({percent}%)')
        self.update_state(state='PROGRESS', meta={
            'step': step, 'current': current, 'total': total,
            'message': message, 'percent': percent,
        })

    def extract_inner_xml(resp_text):
        match = re.search(r'<return>(.*?)</return>', resp_text, re.DOTALL)
        if not match:
            return None
        text = match.group(1)
        return text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

    def cdata_text(elem):
        return (elem.text or '').strip() if elem is not None else ''

    def build_soap(pid, svc):
        return (
            "<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' "
            "xmlns:ser='http://service.rti/'>"
            "<soapenv:Header/><soapenv:Body><ser:invoke>"
            f"<arg0>unitop</arg0><arg1>unitop</arg1><arg2>{svc}</arg2><arg3>@bh='{pid}'</arg3>"
            "</ser:invoke></soapenv:Body></soapenv:Envelope>"
        )

    def convert_photo_path(raw_path):
        """将 Windows 绝对路径转为可访问的图片 URL"""
        if not raw_path:
            return ''
        # C:\JGXTDB\zhao_pian\202105\xxx.jpg → 202105/xxx.jpg
        path = raw_path.replace('\\', '/')
        marker = 'zhao_pian/'
        idx = path.find(marker)
        if idx >= 0:
            relative = path[idx + len(marker):]
        else:
            parts = path.split('/')
            relative = '/'.join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        relative = relative.lstrip('/')
        # 直接访问图片服务器
        return f'http://10.2.50.16/{relative}'

    try:
        # Step 1: 获取罪犯编号
        report('fetch_ids', 0, 100, '正在获取罪犯编号...')
        resp = requests.get(GET_IDS_URL, timeout=30)
        resp.raise_for_status()
        inner_xml = extract_inner_xml(resp.text)
        if not inner_xml:
            report('fetch_ids', 100, 100, '获取罪犯编号失败')
            return {'state': 'FAILURE', 'message': '获取罪犯编号失败'}

        root = ET.fromstring(inner_xml)
        ids = []
        for elem in root.findall('.//zyljbh'):
            x1 = elem.find('x1')
            if x1 is not None and x1.text:
                ids.append(x1.text.strip())

        if not ids:
            report('fetch_ids', 100, 100, '未获取到罪犯编号')
            return {'state': 'FAILURE', 'message': '未获取到罪犯编号'}

        total = len(ids)
        report('fetch_ids', 10, 100, f'获取到 {total} 个罪犯编号')

        # Step 2: 逐个同步基础信息+媒体信息（增量，不清空）
        success = 0
        fail = 0
        created = 0
        updated = 0
        api_ids = set(ids)
        for i, pid in enumerate(ids):
            try:
                # 获取基础信息
                soap = build_soap(pid, 'zf_jbxx_dg')
                r = requests.post(POST_URL, data=soap.encode('utf-8'),
                                  headers={'Content-Type': 'text/xml; charset=utf-8'}, timeout=30)
                r.raise_for_status()
                inner = extract_inner_xml(r.text)
                basic = {}
                if inner:
                    node = ET.fromstring(inner).find('.//zf_jbxx_dg')
                    if node is not None:
                        for child in node:
                            basic[child.tag] = cdata_text(child)

                # 获取媒体信息
                soap = build_soap(pid, 'zf_mt_dg')
                r = requests.post(POST_URL, data=soap.encode('utf-8'),
                                  headers={'Content-Type': 'text/xml; charset=utf-8'}, timeout=30)
                r.raise_for_status()
                inner = extract_inner_xml(r.text)
                media_records = []
                if inner:
                    for elem in ET.fromstring(inner).findall('.//zf_mttz_dg'):
                        media_records.append({
                            'bh': cdata_text(elem.find('bh')),
                            'xm': cdata_text(elem.find('xm')),
                            'mtbmm': cdata_text(elem.find('mtbmm')),
                            'mtlb': cdata_text(elem.find('mtlb')),
                            'xp': cdata_text(elem.find('xp')),
                            'bmmc': cdata_text(elem.find('bmmc')),
                            'bz': cdata_text(elem.find('bz')),
                        })

                # 去重媒体信息
                media_list = []
                seen_xp = set()
                for m in media_records:
                    xp = convert_photo_path(m.get('xp', ''))
                    if xp in seen_xp:
                        continue
                    seen_xp.add(xp)
                    media_list.append({
                        'bh': m.get('bh', ''), 'xm': m.get('xm', ''),
                        'mtbmm': m.get('mtbmm', ''), 'mtlb': m.get('mtlb', ''),
                        'xp': xp, 'bmmc': m.get('bmmc', ''), 'bz': m.get('bz', ''),
                    })

                def safe_int(val):
                    try:
                        return int(val) if val else None
                    except (ValueError, TypeError):
                        return None

                _, is_new = PrisonerArchive.objects.update_or_create(
                    prisoner_no=pid,
                    defaults={
                        'prisoner_name': basic.get('xm', ''),
                        'gender': basic.get('xb', ''),
                        'birth_date': basic.get('csrq', ''),
                        'age': safe_int(basic.get('age')),
                        'id_card': basic.get('sfzh', ''),
                        'nation': basic.get('mz', ''),
                        'education': basic.get('bqwhcd', ''),
                        'marital_status': basic.get('hy', ''),
                        'native_place': basic.get('jg', ''),
                        'address': basic.get('jtmx', ''),
                        'crime': basic.get('zm', ''),
                        'sentence': basic.get('ypxq', ''),
                        'sentence_start': basic.get('rjrq', ''),
                        'sentence_end': basic.get('zr', ''),
                        'prison_area': basic.get('db', ''),
                        'room_no': basic.get('jsh', ''),
                        'bed_no': basic.get('cwh', ''),
                        'status': basic.get('zyxz', ''),
                        'entry_date': basic.get('rjrq', ''),
                        'arrest_org': basic.get('dbjg', ''),
                        'judgment_org': basic.get('pjjg', ''),
                        'judgment_no': basic.get('pjzh', ''),
                        'basic_info': basic,
                        'media_info': media_list,
                    },
                )
                if is_new:
                    created += 1
                else:
                    updated += 1
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f'同步罪犯 {pid} 失败: {e}')

            progress = 10 + int((i + 1) / total * 70)
            report('sync_basic', progress, 100, f'正在同步 {i + 1}/{total}...')

            if (i + 1) % 50 == 0:
                time.sleep(2)

        # 标记已从系统移除的罪犯
        local_ids = set(PrisonerArchive.objects.values_list('prisoner_no', flat=True))
        removed_ids = local_ids - api_ids
        if removed_ids:
            PrisonerArchive.objects.filter(prisoner_no__in=removed_ids).update(is_released=True)
            logger.info(f'标记已移除: {len(removed_ids)} 人')

        report('sync_basic', 80, 100, f'本地同步完成: 成功 {success}, 失败 {fail}, 新增 {created}, 更新 {updated}, 移除 {len(removed_ids)}')

        # Step 3: 同步到大华门禁（直接调用，不走 management command）
        report('sync_dahua', 80, 100, '正在同步到大华门禁...')

        dahua_progress_pct = [80]
        def dahua_progress(msg):
            # 逐步递增进度，让前端能看到变化
            dahua_progress_pct[0] = min(dahua_progress_pct[0] + 1, 95)
            report('sync_dahua', dahua_progress_pct[0], 100, msg)

        face_success, face_fail, skipped, dahua_msg = _sync_to_dahua_direct(dahua_progress)
        report('sync_dahua', 95, 100, dahua_msg)

        # Step 4: 完成
        final_msg = f'同步完成! 本地: 成功 {success}, 失败 {fail} | 大华: 人脸 {face_success}, 跳过 {skipped}'
        report('done', 100, 100, final_msg)
        return {'state': 'SUCCESS', 'message': final_msg}

    except Exception as e:
        logger.error(f'同步任务异常: {e}')
        self.update_state(state='FAILURE', meta={'message': str(e), 'percent': 0})
        raise


@shared_task
def sync_to_handheld_task():
    """每日定时同步罪犯数据到一体机设备

    通过 HTTP 调用 Daphne 的 /user_manage/handheld-sync/trigger/ 端点触发，
    同步逻辑在 Daphne 进程跑（InMemory channel layer 同进程通信）。
    Celery worker 不直接推 WS。
    """
    import requests
    try:
        resp = requests.post(
            'http://127.0.0.1:8000/user_manage/handheld-sync/trigger/',
            json={'full': False},
            timeout=15,
        )
        logger.info('一体机同步已触发: %s %s', resp.status_code, resp.text[:200])
    except Exception as e:
        logger.error('触发一体机同步失败: %s', e)


@shared_task
def check_device_heartbeat():
    """每分钟检查设备心跳，超时标离线；顺带把超时的 pending DeviceSyncLog 标 timeout"""
    from django.utils import timezone
    from apps.users.models import Device, DeviceSyncLog

    threshold = timezone.now() - timedelta(seconds=180)
    offline_count = Device.objects.filter(
        is_online=True, last_seen_at__lt=threshold
    ).update(is_online=False)
    if offline_count:
        logger.info('标记 %d 台设备离线（心跳超时）', offline_count)

    stale_threshold = timezone.now() - timedelta(minutes=10)
    stale_count = DeviceSyncLog.objects.filter(
        status='pending', synced_at__lt=stale_threshold
    ).update(status='timeout', error_msg='等待设备回执超时')
    if stale_count:
        logger.info('标记 %d 条 pending 同步日志为 timeout', stale_count)
