from rest_framework import serializers


class ExitTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    type_name = serializers.CharField(max_length=128, required=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    sort_order = serializers.IntegerField(required=False, default=0)
    status = serializers.ChoiceField(
        choices=[('active', '启用'), ('disabled', '停用')],
        required=False,
        default='active',
    )
