"""
同步每日统计数据到历史记录，并重置每日统计
每天凌晨 00:00 执行
"""
import logging
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.users.models import DailyStatistics, HistoryStatistics

logger = logging.getLogger(__name__)

HISTORY_REASON_FIELDS = [
    ('刑满释放', 'exit_reason_1'),
    ('外出就医', 'exit_reason_2'),
    ('外出教育', 'exit_reason_3'),
    ('离监探亲', 'exit_reason_4'),
    ('押回重审', 'exit_reason_5'),
]


def build_history_reason_counts(reason_stats):
    reason_stats = reason_stats or {}
    return {field: reason_stats.get(reason, 0) for reason, field in HISTORY_REASON_FIELDS}


class Command(BaseCommand):
    help = '同步每日统计数据到历史记录并重置'

    def handle(self, *args, **options):
        today = date.today()

        # 获取昨天的数据
        yesterday = today - timedelta(days=1)
        daily_stats = DailyStatistics.objects.filter(date=yesterday)

        if not daily_stats.exists():
            self.stdout.write(f'昨日({yesterday})没有统计数据，跳过同步')
            return

        # 同步到历史记录
        for stat in daily_stats:
            HistoryStatistics.objects.create(
                prison_area=stat.prison_area,
                prison_area_name=stat.prison_area_name,
                date=yesterday,
                exit_count=stat.exit_count,
                **build_history_reason_counts(stat.reason_stats),
                entry_count=stat.entry_count,
            )
            self.stdout.write(f'已同步: {stat.prison_area} - {yesterday}')

        # 初始化今日统计（为新的一天做准备）
        for stat in daily_stats:
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
            self.stdout.write(f'已重置: {stat.prison_area}')

        self.stdout.write(self.style.SUCCESS(f'完成: {yesterday}数据已同步，{today}统计已重置'))
