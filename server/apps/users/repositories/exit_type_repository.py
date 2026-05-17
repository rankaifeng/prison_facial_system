from apps.users.models import ExitType


class ExitTypeRepository:

    @staticmethod
    def get_all():
        return ExitType.objects.all().order_by('sort_order', 'id')

    @staticmethod
    def get_by_id(exit_type_id):
        try:
            return ExitType.objects.get(id=exit_type_id)
        except ExitType.DoesNotExist:
            return None

    @staticmethod
    def get_type_name(exit_type_id):
        """根据 ID 获取出监原因名称"""
        try:
            exit_type = ExitType.objects.get(id=exit_type_id)
            return exit_type.type_name
        except ExitType.DoesNotExist:
            return None

    @staticmethod
    def exists_by_sibling_name(type_name, parent_id=None, exclude_id=None):
        queryset = ExitType.objects.filter(type_name=type_name)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            queryset = queryset.filter(parent__isnull=True)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    @staticmethod
    def create(**kwargs):
        return ExitType.objects.create(**kwargs)

    @staticmethod
    def update(instance, **kwargs):
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save()
        return instance

    @staticmethod
    def delete(instance):
        instance.delete()
