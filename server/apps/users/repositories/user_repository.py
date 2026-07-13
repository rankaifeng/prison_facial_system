from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()


class UserRepository:

    @staticmethod
    def get_by_id(user_id):
        """根据 ID 获取用户"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户"""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_all(username=None):
        """获取所有用户，可按用户名模糊搜索"""
        queryset = User.objects.all().order_by('-id')
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset

    @staticmethod
    def create(username, password, name='', role='user', prison_id='', prison_name=''):
        """创建用户"""
        role_name_map = {
            'admin': '管理员',
            'user': '普通用户',
        }
        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=name,
            role=role,
            role_name=role_name_map.get(role, '普通用户'),
            prison_id=prison_id,
            prison_name=prison_name,
        )
        return user

    @staticmethod
    def delete(user_id):
        """删除用户"""
        user = UserRepository.get_by_id(user_id)
        if user:
            user.delete()
            return True
        return False

    @staticmethod
    def update(user_id, **kwargs):
        """更新用户"""
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and key != 'password':
                setattr(user, key, value)

        if 'password' in kwargs:
            user.password = make_password(kwargs['password'])

        user.save()
        return user

    @staticmethod
    def exists_by_username(username):
        """检查用户名是否存在"""
        return User.objects.filter(username=username).exists()