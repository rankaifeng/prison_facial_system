import logging
from django.contrib.auth import authenticate
from apps.users.config import create_token
from apps.users.repositories import UserRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):

    @staticmethod
    def login(username, password):
        logger.info(f"Login attempt: username={username}")

        if not username or not password:
            return False, '用户名和密码不能为空', None

        user = authenticate(username=username, password=password)
        if not user:
            logger.warning(f"Login failed: invalid credentials for username={username}")
            return False, '用户名或密码错误', None

        token = create_token(user)
        logger.info(f"Login success: username={username}, user_id={user.id}")

        user_data = {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'role': user.role,
            'role_name': user.role_name,
            'prison_id': user.prison_id,
            'prison_name': user.prison_name,
        }

        return True, '登录成功', {
            'token': token,
            **user_data
        }

    @staticmethod
    def logout(user):
        logger.info(f"Logout: user_id={user.id}")
        return True, '退出成功', None

    @staticmethod
    def verify_token(token):
        from apps.users.config import verify_token as verify
        payload = verify(token)
        if not payload:
            return False, '无效的token', None
        return True, 'token有效', payload

    @staticmethod
    def get_user_info(user):
        return True, '获取成功', {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'role': user.role,
            'role_name': user.role_name,
            'prison_id': user.prison_id,
            'prison_name': user.prison_name,
        }