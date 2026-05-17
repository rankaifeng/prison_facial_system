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

        # 按分监区分组统计
        area_stats = queryset.values(
            'prison_area',
            'prison_area_name'
        ).annotate(
            exit_count=Sum('exit_count'),
            entry_count=Sum('entry_count'),
            exit_reason_1=Sum('exit_reason_1'),
            exit_reason_2=Sum('exit_reason_2'),
            exit_reason_3=Sum('exit_reason_3'),
            exit_reason_4=Sum('exit_reason_4'),
            exit_reason_5=Sum('exit_reason_5'),
        )

        # 按分监区统计的列表（供地图使用）
        area_list = []
        total_exit = 0
        total_entry = 0
        total_reason_1 = 0
        total_reason_2 = 0
        total_reason_3 = 0
        total_reason_4 = 0
        total_reason_5 = 0

        for stat in area_stats:
            exit_cnt = stat['exit_count'] or 0
            entry_cnt = stat['entry_count'] or 0

            # 只返回有数据的出监原因
            reasons = []
            if stat['exit_reason_1']:
                reasons.append({'name': '刑满释放', 'count': stat['exit_reason_1']})
            if stat['exit_reason_2']:
                reasons.append({'name': '外出就医', 'count': stat['exit_reason_2']})
            if stat['exit_reason_3']:
                reasons.append({'name': '外出教育', 'count': stat['exit_reason_3']})
            if stat['exit_reason_4']:
                reasons.append({'name': '离监探亲', 'count': stat['exit_reason_4']})
            if stat['exit_reason_5']:
                reasons.append({'name': '押回重审', 'count': stat['exit_reason_5']})

            area_item = {
                'prison_area': stat['prison_area'],
                'prison_area_name': stat['prison_area_name'],
                'exit_count': exit_cnt,
                'entry_count': entry_cnt,
                'net_exit': exit_cnt - entry_cnt,
                'reasons': reasons
            }
            area_list.append(area_item)

            total_exit += exit_cnt
            total_entry += entry_cnt
            total_reason_1 += stat['exit_reason_1'] or 0
            total_reason_2 += stat['exit_reason_2'] or 0
            total_reason_3 += stat['exit_reason_3'] or 0
            total_reason_4 += stat['exit_reason_4'] or 0
            total_reason_5 += stat['exit_reason_5'] or 0

        # 只返回有数据的汇总出监原因
        total_reasons = []
        if total_reason_1:
            total_reasons.append({'name': '刑满释放', 'count': total_reason_1})
        if total_reason_2:
            total_reasons.append({'name': '外出就医', 'count': total_reason_2})
        if total_reason_3:
            total_reasons.append({'name': '外出教育', 'count': total_reason_3})
        if total_reason_4:
            total_reasons.append({'name': '离监探亲', 'count': total_reason_4})
        if total_reason_5:
            total_reasons.append({'name': '押回重审', 'count': total_reason_5})

        # 汇总统计
        result = {
            'total': {
                'exit_count': total_exit,
                'entry_count': total_entry,
                'net_exit': total_exit - total_entry,
                'reasons': total_reasons
            },
            'by_area': area_list,
        }

        return True, '获取成功', result