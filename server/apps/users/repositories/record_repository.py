from apps.users.models import ExitEntryRecord


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
    def filter(type=None, start_date=None, end_date=None, prison_area=None):
        """条件筛选记录"""
        queryset = ExitEntryRecord.objects.all()

        if type:
            queryset = queryset.filter(type=type)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if prison_area:
            queryset = queryset.filter(prison_area=prison_area)

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
    def count_by_type(type):
        """统计某类型记录数量"""
        return ExitEntryRecord.objects.filter(type=type).count()

    @staticmethod
    def get_recent_records(limit=10):
        """获取最近记录"""
        return ExitEntryRecord.objects.all().order_by('-created_at')[:limit]