import logging
from django.contrib.auth import authenticate
from apps.users.repositories import UserRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AccountService(BaseService):

    @staticmethod
    def list_accounts(username=None):
        users = UserRepository.get_all(username=username)
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'name': user.first_name or user.username,
                'role': user.role,
                'role_name': user.role_name,
                'prison_id': user.prison_id,
                'prison_name': user.prison_name,
                'status': 'active',
                'created_at': user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
            })
        return True, '获取成功', data

    @staticmethod
    def create_account(username, password='123456', name='', role='user', prison_id='', prison_name=''):
        if UserRepository.exists_by_username(username):
            return False, '账号已存在', None

        user = UserRepository.create(
            username=username,
            password=password,
            name=name,
            role=role,
            prison_id=prison_id,
            prison_name=prison_name,
        )
        logger.info(f"Account created: username={username}, id={user.id}")

        return True, '新增成功', {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'role': user.role,
            'role_name': user.role_name,
            'prison_id': user.prison_id,
            'prison_name': user.prison_name,
        }

    @staticmethod
    def delete_account(account_id):
        user = UserRepository.get_by_id(account_id)
        if not user:
            return False, '账号不存在', None

        if user.username == 'admin':
            return False, '不能删除管理员账号', None

        UserRepository.delete(account_id)
        logger.info(f"Account deleted: id={account_id}")

        return True, '删除成功', None

    @staticmethod
    def get_account(account_id):
        user = UserRepository.get_by_id(account_id)
        if not user:
            return False, '账号不存在', None

        return True, '获取成功', {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'role': user.role,
            'role_name': user.role_name,
            'prison_id': user.prison_id,
            'prison_name': user.prison_name,
        }

    @staticmethod
    def get_password(admin_user, admin_password, account_id):
        if not admin_user.check_password(admin_password):
            return False, '管理员密码错误', None

        user = UserRepository.get_by_id(account_id)
        if not user:
            return False, '账号不存在', None

        return True, '获取成功', {'password': user.plain_password or ''}

    @staticmethod
    def update_account(account_id, **kwargs):
        user = UserRepository.update(account_id, **kwargs)
        if not user:
            return False, '账号不存在', None

        logger.info(f"Account updated: id={account_id}")

        return True, '更新成功', {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'role': user.role,
            'role_name': user.role_name,
            'prison_id': user.prison_id,
            'prison_name': user.prison_name,
        }