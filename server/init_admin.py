#!/usr/bin/env python
"""
初始化管理员账号脚本
使用方法: python init_admin.py
"""
import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from apps.users.models import User


def create_admin():
    """创建默认管理员账号"""
    username = 'admin'
    password = 'admin123'

    if User.objects.filter(username=username).exists():
        print(f'管理员账号 {username} 已存在')
        return

    User.objects.create(
        username=username,
        password=make_password(password),
        first_name='管理员',
        role='admin',
        role_name='管理员',
        prison_id='',
        prison_name='',
    )
    print(f'管理员账号创建成功: {username}/{password}')


if __name__ == '__main__':
    create_admin()