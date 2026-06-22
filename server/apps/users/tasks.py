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
        call_command('sync_prisoner_data', '--real-api')
        logger.info('罪犯数据同步完成')
        return '罪犯数据同步完成'
    except Exception as e:
        logger.error(f'罪犯数据同步失败: {e}')
        return f'同步失败: {e}'
