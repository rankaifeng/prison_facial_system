from apps.users.models import ExitEntryRecord
from datetime import datetime


class RecordRepository:

    @staticmethod
    def get_by_id(record_id):
        """根据 ID 获取记录"""
        try:
            return ExitEntryRecord.objects.get(id=record_id)
        except ExitEntryRecord.DoesNotExist:
            return None

    @staticmethod
    def get_all():
        """获取所有记录"""
        return ExitEntryRecord.objects.all().order_by('-created_at')

    @staticmethod
    def filter(type=None, start_timestamp=None, end_timestamp=None, prison_area=None,
              prisoner_name=None, prisoner_no=None, reason=None):
        """条件筛选记录"""
        queryset = ExitEntryRecord.objects.all()

        if type:
            queryset = queryset.filter(type=type)
        if start_timestamp:
            # 支持字符串或整数类型的时间戳
            if isinstance(start_timestamp, str):
                start_timestamp = int(start_timestamp)
            start_date = datetime.fromtimestamp(start_timestamp / 1000).date() if start_timestamp else None
            if type == 'exit':
                queryset = queryset.filter(exit_date__gte=start_date)
            elif type == 'entry':
                queryset = queryset.filter(entry_date__gte=start_date)
            else:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(exit_date__gte=start_date) | Q(entry_date__gte=start_date)
                )
        if end_timestamp:
            if isinstance(end_timestamp, str):
                end_timestamp = int(end_timestamp)
            end_date = datetime.fromtimestamp(end_timestamp / 1000).date() if end_timestamp else None
            if type == 'exit':
                queryset = queryset.filter(exit_date__lte=end_date)
            elif type == 'entry':
                queryset = queryset.filter(entry_date__lte=end_date)
            else:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(exit_date__lte=end_date) | Q(entry_date__lte=end_date)
                )
        if prison_area:
            from django.db.models import Q
            from apps.users.dict import get_prison_area_name
            area_name = get_prison_area_name(prison_area)
            q = Q(prison_area=prison_area) | Q(prison_area_name=prison_area)
            if area_name:
                q = q | Q(prison_area=area_name) | Q(prison_area_name=area_name)
            queryset = queryset.filter(q)
        if prisoner_name:
            queryset = queryset.filter(prisoner_name__icontains=prisoner_name)
        if prisoner_no:
            queryset = queryset.filter(prisoner_no=prisoner_no)
        if reason:
            queryset = queryset.filter(reason=reason)

        return queryset.order_by('-created_at')

    @staticmethod
    def create(**kwargs):
        """创建记录"""
        return ExitEntryRecord.objects.create(**kwargs)

    @staticmethod
    def get_by_prisoner_no(prisoner_no):
        """根据罪犯编号获取记录"""
        return ExitEntryRecord.objects.filter(prisoner_no=prisoner_no).order_by('-created_at')

    @staticmethod
    def get_last_exit_by_prisoner_no(prisoner_no):
        """获取该罪犯的最后一条出监记录"""
        try:
            return ExitEntryRecord.objects.filter(
                prisoner_no=prisoner_no,
                type='exit'
            ).order_by('-created_at').first()
        except ExitEntryRecord.DoesNotExist:
            return None

    @staticmethod
    def count_by_type(type):
        """统计某类型记录数量"""
        return ExitEntryRecord.objects.filter(type=type).count()

    @staticmethod
    def get_recent_records(limit=10):
        """获取最近记录"""
        return ExitEntryRecord.objects.all().order_by('-created_at')[:limit]

    @staticmethod
    def get_active_exit_messages(prison_area=None):
        """获取活跃的出监消息（未入监的）"""
        queryset = ExitEntryRecord.objects.filter(
            type='exit',
            status='completed'
        )
        if prison_area:
            from django.db.models import Q
            from apps.users.dict import get_prison_area_name
            area_name = get_prison_area_name(prison_area)
            q = Q(prison_area=prison_area) | Q(prison_area_name=prison_area)
            if area_name:
                q = q | Q(prison_area=area_name) | Q(prison_area_name=area_name)
            queryset = queryset.filter(q)
        return queryset.order_by('-created_at')

    @staticmethod
    def has_entry_record(prisoner_no):
        """检查是否存在入监记录"""
        return ExitEntryRecord.objects.filter(
            prisoner_no=prisoner_no,
            type='entry',
            status='completed'
        ).exists()