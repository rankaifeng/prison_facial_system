"""
Celery 定时任务
"""
import logging
from datetime import date, timedelta
from celery import shared_task
from apps.users.models import DailyStatistics, HistoryStatistics

logger = logging.getLogger(__name__)


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
            exit_reason_1=stat.exit_reason_1,
            exit_reason_2=stat.exit_reason_2,
            exit_reason_3=stat.exit_reason_3,
            exit_reason_4=stat.exit_reason_4,
            exit_reason_5=stat.exit_reason_5,
            entry_count=stat.entry_count,
            in_prison_count=stat.in_prison_count,
            work_count=stat.work_count,
        )
        synced_count += 1

        # 重置为新的一天
        stat.exit_count = 0
        stat.exit_reason_1 = 0
        stat.exit_reason_2 = 0
        stat.exit_reason_3 = 0
        stat.exit_reason_4 = 0
        stat.exit_reason_5 = 0
        stat.entry_count = 0
        stat.date = today
        stat.save()
        reset_count += 1

    message = f'完成: {yesterday}数据已同步({synced_count}条)，{today}统计已重置({reset_count}条)'
    logger.info(message)
    return message