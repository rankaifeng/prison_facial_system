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

        # 获取所有出监原因（按 id 排序）
        from apps.users.models import ExitType
        exit_types = ExitType.objects.filter(status='active').order_by('id')
        all_reasons = [et.type_name for et in exit_types]

        # 如果没有配置出监原因，使用默认的
        if not all_reasons:
            all_reasons = ['刑满释放', '外出就医', '外出教育', '离监探亲', '押回重审']

        # 按分监区分组统计
        area_stats = queryset.values(
            'prison_area',
            'prison_area_name'
        ).annotate(
            exit_count=Sum('exit_count'),
            entry_count=Sum('entry_count'),
            in_prison_count=Sum('in_prison_count'),
        )

        # 汇总 reason_stats
        total_reason_stats = {reason: 0 for reason in all_reasons}

        # 按分监区统计的列表（供地图使用）
        area_list = []
        total_exit = 0
        total_entry = 0
        total_in_prison = 0

        for stat in area_stats:
            exit_cnt = stat['exit_count'] or 0
            entry_cnt = stat['entry_count'] or 0
            in_prison_cnt = stat['in_prison_count'] or 0

            total_exit += exit_cnt
            total_entry += entry_cnt
            total_in_prison += in_prison_cnt

            # 获取该分监区的 reason_stats JSONField
            db_stat = queryset.filter(prison_area=stat['prison_area']).first()
            reason_stats = db_stat.reason_stats if db_stat and db_stat.reason_stats else {}

            # 按分监区的统计，包含各出监原因
            area_reasons = []
            for reason in all_reasons:
                count = reason_stats.get(reason, 0)
                area_reasons.append({'name': reason, 'count': count})
                if reason in total_reason_stats:
                    total_reason_stats[reason] += count

            area_item = {
                'prison_area': stat['prison_area'],
                'prison_area_name': stat['prison_area_name'],
                'exit_count': exit_cnt,
                'entry_count': entry_cnt,
                'in_prison_count': in_prison_cnt,
                'reasons': area_reasons
            }
            area_list.append(area_item)

        # 汇总统计
        total_reasons = [{'name': reason, 'count': total_reason_stats[reason]} for reason in all_reasons]

        result = {
            'total': {
                'exit_count': total_exit,
                'entry_count': total_entry,
                'in_prison_count': total_in_prison,
                'reasons': total_reasons
            },
            'by_area': area_list,
        }

        return True, '获取成功', result