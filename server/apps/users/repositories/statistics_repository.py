from apps.users.models import DailyStatistics, HistoryStatistics
from datetime import date


class StatisticsRepository:

    @staticmethod
    def get_daily_stats(prison_area=None, target_date=None):
        """获取每日统计"""
        if target_date is None:
            target_date = date.today()

        queryset = DailyStatistics.objects.filter(date=target_date)
        if prison_area:
            queryset = queryset.filter(prison_area=prison_area)

        return queryset

    @staticmethod
    def get_or_create_daily_stats(prison_area, prison_area_name, target_date=None):
        """获取或创建每日统计"""
        if target_date is None:
            target_date = date.today()

        stat, created = DailyStatistics.objects.get_or_create(
            prison_area=prison_area,
            date=target_date,
            defaults={
                'prison_area_name': prison_area_name,
                'exit_count': 0,
                'entry_count': 0,
                'in_prison_count': 0,
                'work_count': 0,
                'reason_stats': {},
            }
        )
        return stat

    @staticmethod
    def update_daily_stats(stat, **kwargs):
        """更新每日统计"""
        for key, value in kwargs.items():
            if hasattr(stat, key):
                setattr(stat, key, value)
        stat.save()
        return stat

    @staticmethod
    def get_history_stats(start_date=None, end_date=None, prison_area=None):
        """获取历史统计"""
        queryset = HistoryStatistics.objects.all()

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if prison_area:
            queryset = queryset.filter(prison_area=prison_area)

        return queryset.order_by('-date')

    @staticmethod
    def create_history_stats(**kwargs):
        """创建历史统计"""
        return HistoryStatistics.objects.create(**kwargs)