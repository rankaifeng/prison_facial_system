import logging
from datetime import date, datetime, timedelta
from .base_service import BaseService

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


class StatisticsService(BaseService):

    @staticmethod
    def check_and_reset_daily_stats():
        """
        检测是否需要重置当日统计（本地开发环境没有 Celery Beat 时用）。
        每次请求统计时调用，如果当日 DailyStatistics 不存在则自动执行重置。
        生产环境 Celery Beat 凌晨已执行过，当日数据存在，跳过。
        """
        from apps.users.models import DailyStatistics, HistoryStatistics, TodayExitRecord

        today = date.today()
        if DailyStatistics.objects.filter(date=today).exists():
            return  # 当日数据已存在，无需重置

        yesterday = today - timedelta(days=1)

        # 清空今日出监记录
        deleted_count, _ = TodayExitRecord.objects.all().delete()
        if deleted_count:
            logger.info(f'[auto-reset] 已清空今日出监记录: {deleted_count} 条')

        # 将昨日统计同步到历史记录
        daily_stats = DailyStatistics.objects.filter(date=yesterday)
        for stat in daily_stats:
            HistoryStatistics.objects.create(
                prison_area=stat.prison_area,
                prison_area_name=stat.prison_area_name,
                date=yesterday,
                exit_count=stat.exit_count,
                **_build_history_reason_counts(stat.reason_stats),
                entry_count=stat.entry_count,
            )
            # 创建今日统计（计数归零，在押人数保留）
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

        if daily_stats:
            logger.info(f'[auto-reset] 昨日数据已同步，今日统计已重置 ({len(daily_stats)} 个监区)')

    @staticmethod
    def get_realtime_statistics(prison_area=None):
        StatisticsService.check_and_reset_daily_stats()
        from apps.users.models import PrisonerArchive, ExitType, ExitEntryRecord, TodayExitRecord
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

        # ========== 从今日出监记录表获取出监数据 ==========
        today_records = TodayExitRecord.objects.all()
        if prison_area:
            # prison_area 参数是 ID（"1"-"7"），TodayExitRecord.prison_area 字段存的也是 ID
            today_records = today_records.filter(prison_area=prison_area)

        # 按监区分组统计出监人数
        area_exit_stats = today_records.values('prison_area_name').annotate(
            exit_count=Count('id')
        )

        # 按出监原因分组统计
        reason_stats = today_records.values('exit_reason').annotate(
            count=Count('id')
        )
        total_reason_stats = {reason: 0 for reason in all_reasons}
        for item in reason_stats:
            if item['exit_reason'] in total_reason_stats:
                total_reason_stats[item['exit_reason']] = item['count']

        total_exit = today_records.count()

        # 年度出监统计（按监区名称归一化合并）
        from datetime import timedelta
        year_start = date(today.year, 1, 1)
        tomorrow = today + timedelta(days=1)
        from apps.users.dict import get_prison_area_name, get_prison_area_id

        yearly_by_area = {}  # key=监区名称, value=count
        yearly_records = ExitEntryRecord.objects.filter(
            type='exit', exit_date__gte=year_start, exit_date__lt=tomorrow
        ).values('prisoner_no', 'prison_area', 'prison_area_name')

        # 预加载罪犯档案的监区信息（用于回退）
        prisoner_nos = [r['prisoner_no'] for r in yearly_records if r['prisoner_no']]
        archive_area_map_cache = {}
        if prisoner_nos:
            for pa in PrisonerArchive.objects.filter(prisoner_no__in=prisoner_nos).values('prisoner_no', 'prison_area'):
                if pa['prison_area']:
                    archive_area_map_cache[pa['prisoner_no']] = pa['prison_area']

        for item in yearly_records:
            # 归一化：优先用 prison_area_name，没有则从 prison_area ID 转换，最后回退到档案监区
            name = item['prison_area_name'] or get_prison_area_name(item['prison_area'])
            if not name:
                name = archive_area_map_cache.get(item['prisoner_no'], '')
            if not name:
                continue
            yearly_by_area[name] = yearly_by_area.get(name, 0) + 1

        # 构建 yearly_stats，同时用名称和 ID 作为 key
        yearly_stats = {}
        for name, count in yearly_by_area.items():
            entry = {'yearly_exit': count, 'prison_area_name': name}
            yearly_stats[name] = entry
            area_id = get_prison_area_id(name)
            if area_id:
                yearly_stats[str(area_id)] = entry

        # 按监区构建出监原因分布
        area_reason_map = {}
        for record in today_records.values('prison_area_name', 'exit_reason'):
            area_name = record['prison_area_name']
            reason = record['exit_reason']
            if area_name not in area_reason_map:
                area_reason_map[area_name] = {}
            area_reason_map[area_name][reason] = area_reason_map[area_name].get(reason, 0) + 1

        processed_areas = set()
        area_list = []

        for stat in area_exit_stats:
            area_name = stat['prison_area_name']
            exit_cnt = stat['exit_count'] or 0
            area_id = get_prison_area_id(area_name)
            area_key = str(area_id) if area_id else area_name

            area_reasons = []
            for reason in all_reasons:
                count = area_reason_map.get(area_name, {}).get(reason, 0)
                area_reasons.append({'name': reason, 'count': count})

            area_list.append({
                'prison_area': area_key,
                'prison_area_name': area_name,
                'in_prison_count': archive_area_map.get(area_name, 0),
                'exit_count': exit_cnt,
                'entry_count': 0,
                'yearly_exit_count': yearly_stats.get(area_name, {}).get('yearly_exit', 0),
                'reasons': area_reasons
            })
            processed_areas.add(area_name)

        # 补充档案库中有但今日出监记录中没有的监区
        for area_name, count in archive_area_map.items():
            if area_name not in processed_areas:
                area_id = get_prison_area_id(area_name)
                area_key = str(area_id) if area_id else area_name
                yearly_match = yearly_stats.get(area_name)
                area_list.append({
                    'prison_area': area_key,
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
                'entry_count': 0,
                'in_prison_count': total_in_prison,
                'reasons': total_reasons
            },
            'by_area': area_list,
        }

        return True, '获取成功', result

    @staticmethod
    def get_work_statistics(prison_area=None):
        StatisticsService.check_and_reset_daily_stats()
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
