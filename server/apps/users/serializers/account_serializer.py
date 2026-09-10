from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    class Meta:
        from apps.users.models import User
        model = User
        fields = ['id', 'username', 'role', 'role_name', 'prison_id', 'prison_name']


class AccountCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=64, required=True, label='账号')
    password = serializers.CharField(max_length=128, required=False, write_only=True, label='密码')
    name = serializers.CharField(max_length=64, required=False, label='姓名')
    role = serializers.CharField(max_length=32, required=False, label='角色')
    prison_id = serializers.CharField(max_length=32, required=False, label='所属监狱ID')
    prison_name = serializers.CharField(max_length=128, required=False, label='所属监狱名称')