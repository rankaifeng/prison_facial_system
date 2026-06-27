"""
Celery 定时任务
"""
import logging
from datetime import date, timedelta
from celery import shared_task
from apps.users.models import DailyStatistics, HistoryStatistics

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
            stall_timeout=8,
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


@shared_task(bind=True)
def sync_prisoner_data_with_progress(self):
    """手动同步罪犯数据（带进度报告）"""
    import os, requests, re, time, base64
    from xml.etree import ElementTree as ET
    from django.conf import settings
    from apps.users.models import PrisonerArchive

    API_BASE = os.getenv('RTI_API_BASE', 'http://10.2.50.16:4092')
    PHOTO_BASE_URL = os.getenv('PHOTO_BASE_URL', '').rstrip('/')
    GET_IDS_URL = f"{API_BASE}/rti/service/invoke/arg0/unitop/arg1/unitop/arg2/zf_zyljbh/arg3/@zy='zy'"
    POST_URL = f'{API_BASE}/rti/service'

    def report(step, current, total, message):
        percent = int(current / total * 100) if total > 0 else 0
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
        if not raw_path:
            return ''
        path = raw_path.replace('\\', '/')
        marker = 'zhao_pian/'
        idx = path.find(marker)
        relative = path[idx + len(marker):] if idx >= 0 else '/'.join(path.split('/')[-2:])
        relative = relative.lstrip('/')
        if PHOTO_BASE_URL:
            return f'{PHOTO_BASE_URL}/{relative}'
        from urllib.parse import urlparse
        parsed = urlparse(API_BASE)
        return f'{parsed.scheme}://{parsed.hostname}/{relative}'

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

        # Step 2: 逐个同步基础信息+媒体信息
        success = 0
        fail = 0
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

                PrisonerArchive.objects.update_or_create(
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
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f'同步罪犯 {pid} 失败: {e}')

            progress = 10 + int((i + 1) / total * 70)
            report('sync_basic', progress, 100, f'正在同步 {i + 1}/{total}...')

            if (i + 1) % 50 == 0:
                time.sleep(2)

        report('sync_basic', 80, 100, f'同步完成: 成功 {success}, 失败 {fail}')

        # Step 3: 同步到大华门禁
        report('sync_dahua', 80, 100, '正在同步到大华门禁...')
        try:
            from django.core.management import call_command
            call_command('sync_prisoner_data', '--dahua')
            report('sync_dahua', 95, 100, '大华门禁同步完成')
        except Exception as e:
            logger.error(f'大华门禁同步失败: {e}')
            report('sync_dahua', 95, 100, f'大华门禁同步失败: {e}')

        # Step 4: 完成
        report('done', 100, 100, f'同步完成! 成功 {success}, 失败 {fail}')
        return {'state': 'SUCCESS', 'message': f'同步完成! 成功 {success}, 失败 {fail}'}

    except Exception as e:
        logger.error(f'同步任务异常: {e}')
        self.update_state(state='FAILURE', meta={'message': str(e), 'percent': 0})
        raise
