import logging
from datetime import date
from django.db.models import Sum
from apps.users.repositories import StatisticsRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)

# 出监原因映射
EXIT_REASON_MAP = {
    'exit_reason_1': '刑满释放',
    'exit_reason_2': '外出就医',
    'exit_reason_3': '外出教育',
    'exit_reason_4': '离监探亲',
    'exit_reason_5': '押回重审',
}


class StatisticsService(BaseService):

    @staticmethod
    def get_realtime_statistics(prison_area=None):
        today = date.today()
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        # 获取所有出监原因
        from apps.users.models import ExitType
        all_exit_types = ExitType.objects.filter(status='active').order_by('sort_order', 'id')
        all_reasons = [et.type_name for et in all_exit_types]

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
            exit_reason_1=Sum('exit_reason_1'),
            exit_reason_2=Sum('exit_reason_2'),
            exit_reason_3=Sum('exit_reason_3'),
            exit_reason_4=Sum('exit_reason_4'),
            exit_reason_5=Sum('exit_reason_5'),
        )

        # 原因映射
        reason_key_map = {
            '刑满释放': 'exit_reason_1',
            '外出就医': 'exit_reason_2',
            '外出教育': 'exit_reason_3',
            '离监探亲': 'exit_reason_4',
            '押回重审': 'exit_reason_5',
        }

        # 按分监区统计的列表（供地图使用）
        area_list = []
        total_exit = 0
        total_entry = 0
        total_in_prison = 0
        total_by_reason = {reason: 0 for reason in all_reasons}

        for stat in area_stats:
            exit_cnt = stat['exit_count'] or 0
            entry_cnt = stat['entry_count'] or 0
            in_prison_cnt = stat['in_prison_count'] or 0

            # 按分监区的统计，包含各出监原因
            area_reasons = []
            for reason in all_reasons:
                reason_key = reason_key_map.get(reason, f'exit_reason_{all_reasons.index(reason) + 1}')
                count = stat.get(reason_key, 0) or 0
                area_reasons.append({'name': reason, 'count': count})
                total_by_reason[reason] += count

            area_item = {
                'prison_area': stat['prison_area'],
                'prison_area_name': stat['prison_area_name'],
                'exit_count': exit_cnt,
                'entry_count': entry_cnt,
                'in_prison_count': in_prison_cnt,
                'reasons': area_reasons
            }
            area_list.append(area_item)

            total_exit += exit_cnt
            total_entry += entry_cnt
            total_in_prison += in_prison_cnt

        # 汇总统计
        total_reasons = [{'name': reason, 'count': total_by_reason[reason]} for reason in all_reasons]

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