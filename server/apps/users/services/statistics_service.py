import logging
from datetime import date
from django.db.models import Sum
from apps.users.repositories import StatisticsRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class StatisticsService(BaseService):

    @staticmethod
    def get_realtime_statistics(prison_area=None):
        today = date.today()
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        stats = queryset.aggregate(
            total=Sum('exit_count'),
            entry_total=Sum('entry_count'),
            exit_reason_1=Sum('exit_reason_1'),
            exit_reason_2=Sum('exit_reason_2'),
            exit_reason_3=Sum('exit_reason_3'),
            exit_reason_4=Sum('exit_reason_4'),
            exit_reason_5=Sum('exit_reason_5'),
        )

        exit_count = stats['total'] or 0
        entry_count = stats['entry_total'] or 0

        result = {
            'total': exit_count - entry_count,  # 出监净人数 = 出监 - 入监
            'exit_count': exit_count,            # 出监总人数
            'entry_count': entry_count,          # 入监总人数
            'exit_reason_1': stats['exit_reason_1'] or 0,  # 刑满释放
            'exit_reason_2': stats['exit_reason_2'] or 0,  # 外出就医
            'exit_reason_3': stats['exit_reason_3'] or 0,  # 外出教育
            'exit_reason_4': stats['exit_reason_4'] or 0,  # 离监探亲
            'exit_reason_5': stats['exit_reason_5'] or 0,  # 押回重审
        }

        return True, '获取成功', result

    @staticmethod
    def get_work_statistics(prison_area=None):
        today = date.today()
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        work_stats = queryset.values('date').annotate(
            total=Sum('exit_count'),
            workCount=Sum('work_count')
        ).order_by('-date')

        return True, '获取成功', list(work_stats)

    @staticmethod
    def get_daily_statistics(prison_area=None):
        today = date.today()
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        data = []
        for stat in queryset:
            data.append({
                'prison_area': stat.prison_area,
                'prison_area_name': stat.prison_area_name,
                'exit_count': stat.exit_count,
                'exit_reason_1': stat.exit_reason_1,
                'exit_reason_2': stat.exit_reason_2,
                'exit_reason_3': stat.exit_reason_3,
                'exit_reason_4': stat.exit_reason_4,
                'exit_reason_5': stat.exit_reason_5,
                'entry_count': stat.entry_count,
                'in_prison_count': stat.in_prison_count,
            })

        return True, '获取成功', data

    @staticmethod
    def get_history_statistics(start_date=None, end_date=None, prison_area=None):
        queryset = StatisticsRepository.get_history_stats(start_date, end_date, prison_area)

        data = []
        for stat in queryset:
            data.append({
                'date': stat.date,
                'prison_area': stat.prison_area,
                'prison_area_name': stat.prison_area_name,
                'exit_count': stat.exit_count,
                'exit_reason_1': stat.exit_reason_1,
                'exit_reason_2': stat.exit_reason_2,
                'exit_reason_3': stat.exit_reason_3,
                'exit_reason_4': stat.exit_reason_4,
                'exit_reason_5': stat.exit_reason_5,
                'entry_count': stat.entry_count,
            })

        return True, '获取成功', data

    @staticmethod
    def update_daily_statistics(prison_area, prison_area_name, target_date=None):
        return StatisticsRepository.get_or_create_daily_stats(prison_area, prison_area_name, target_date)