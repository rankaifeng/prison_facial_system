import logging
from datetime import date, datetime
from django.db.models import Sum
from apps.users.repositories import StatisticsRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class StatisticsService(BaseService):

    @staticmethod
    def get_realtime_statistics(prison_area=None):
        from apps.users.models import PrisonerArchive, ExitType, ExitEntryRecord
        from django.db.models import Count

        today = date.today()

        # ========== 从档案库表获取实时在监人数 ==========
        archive_qs = PrisonerArchive.objects.all()
        total_in_prison = archive_qs.count()

        # 按监区分组统计在监人数（档案表的 prison_area 字段，值来自 XML 的 db 字段）
        archive_by_area = archive_qs.values('prison_area').annotate(count=Count('id')).order_by('prison_area')
        archive_area_map = {item['prison_area']: item['count'] for item in archive_by_area if item['prison_area']}

        # ========== 获取出监原因 ==========
        exit_types = ExitType.objects.filter(status='active').order_by('id')
        all_reasons = [et.type_name for et in exit_types]
        if not all_reasons:
            all_reasons = ['刑满释放', '外出就医', '外出教育', '离监探亲', '押回重审']

        # ========== 从每日统计表获取出入监数据 ==========
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        area_stats = queryset.values(
            'prison_area', 'prison_area_name'
        ).annotate(
            exit_count=Sum('exit_count'),
            entry_count=Sum('entry_count'),
        )

        total_reason_stats = {reason: 0 for reason in all_reasons}
        area_list = []
        total_exit = 0
        total_entry = 0

        # 年度出监统计
        year_start = date(today.year, 1, 1)
        yearly_stats = {}
        yearly_records = ExitEntryRecord.objects.filter(
            type='exit', exit_date__gte=year_start, exit_date__lte=today
        ).values('prison_area', 'prison_area_name').annotate(yearly_exit=Count('id'))

        for item in yearly_records:
            yearly_stats[item['prison_area']] = {
                'yearly_exit': item['yearly_exit'],
                'prison_area_name': item['prison_area_name']
            }

        processed_areas = set()
        if area_stats:
            for stat in area_stats:
                exit_cnt = stat['exit_count'] or 0
                entry_cnt = stat['entry_count'] or 0
                total_exit += exit_cnt
                total_entry += entry_cnt

                db_stat = queryset.filter(prison_area=stat['prison_area']).first()
                reason_stats = db_stat.reason_stats if db_stat and db_stat.reason_stats else {}

                area_reasons = []
                for reason in all_reasons:
                    count = reason_stats.get(reason, 0)
                    area_reasons.append({'name': reason, 'count': count})
                    if reason in total_reason_stats:
                        total_reason_stats[reason] += count

                area_name = stat['prison_area_name']
                area_list.append({
                    'prison_area': stat['prison_area'],
                    'prison_area_name': area_name,
                    'in_prison_count': archive_area_map.get(area_name, 0),
                    'exit_count': exit_cnt,
                    'entry_count': entry_cnt,
                    'yearly_exit_count': yearly_stats.get(stat['prison_area'], {}).get('yearly_exit', 0),
                    'reasons': area_reasons
                })
                processed_areas.add(stat['prison_area'])

        # 补充档案库中有但每日统计中没有的监区
        for area_name, count in archive_area_map.items():
            if area_name not in processed_areas:
                yearly_match = next((v for k, v in yearly_stats.items() if v['prison_area_name'] == area_name), None)
                area_list.append({
                    'prison_area': area_name,
                    'prison_area_name': area_name,
                    'in_prison_count': count,
                    'exit_count': 0,
                    'entry_count': 0,
                    'yearly_exit_count': yearly_match['yearly_exit'] if yearly_match else 0,
                    'reasons': []
                })

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

    @staticmethod
    def get_work_statistics(prison_area=None):
        today = date.today()
        queryset = StatisticsRepository.get_daily_stats(prison_area, today)

        area_stats = queryset.values(
            'prison_area',
            'prison_area_name'
        ).annotate(
            work_count=Sum('work_count'),
            in_prison_count=Sum('in_prison_count'),
            exit_count=Sum('exit_count'),
            entry_count=Sum('entry_count'),
        )

        by_area = []
        total_work = 0
        total_in_prison = 0
        total_exit = 0
        total_entry = 0

        for stat in area_stats:
            work_count = stat['work_count'] or 0
            in_prison_count = stat['in_prison_count'] or 0
            exit_count = stat['exit_count'] or 0
            entry_count = stat['entry_count'] or 0

            total_work += work_count
            total_in_prison += in_prison_count
            total_exit += exit_count
            total_entry += entry_count

            by_area.append({
                'prison_area': stat['prison_area'],
                'prison_area_name': stat['prison_area_name'],
                'work_count': work_count,
                'in_prison_count': in_prison_count,
                'exit_count': exit_count,
                'entry_count': entry_count,
            })

        return True, '获取成功', {
            'total': {
                'work_count': total_work,
                'in_prison_count': total_in_prison,
                'exit_count': total_exit,
                'entry_count': total_entry,
            },
            'by_area': by_area,
        }
