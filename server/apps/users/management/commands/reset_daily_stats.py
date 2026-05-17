"""
同步每日统计数据到历史记录，并重置每日统计
每天凌晨 00:00 执行
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.users.models import DailyStatistics, HistoryStatistics

logger = logging.getLogger(__name__)


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
                exit_reason_1=stat.exit_reason_1,
                exit_reason_2=stat.exit_reason_2,
                exit_reason_3=stat.exit_reason_3,
                exit_reason_4=stat.exit_reason_4,
                exit_reason_5=stat.exit_reason_5,
                entry_count=stat.entry_count,
                in_prison_count=stat.in_prison_count,
                work_count=stat.work_count,
            )
            self.stdout.write(f'已同步: {stat.prison_area} - {yesterday}')

        # 重置今日统计（为新的一天做准备）
        for stat in daily_stats:
            stat.exit_count = 0
            stat.exit_reason_1 = 0
            stat.exit_reason_2 = 0
            stat.exit_reason_3 = 0
            stat.exit_reason_4 = 0
            stat.exit_reason_5 = 0
            stat.entry_count = 0
            stat.date = today
            stat.save()
            self.stdout.write(f'已重置: {stat.prison_area}')

        self.stdout.write(self.style.SUCCESS(f'完成: {yesterday}数据已同步，{today}统计已重置'))