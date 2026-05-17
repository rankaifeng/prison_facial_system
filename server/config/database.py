"""
Django 数据库配置文件
支持多数据源配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


def get_database_config(db_name='default', custom_config=None):
    """
    获取数据库配置
    支持多数据源配置外部数据库

    用法:
        # 默认数据库
        DATABASES = {
            'default': get_database_config('default')
        }

        # 外部数据库
        DATABASES = {
            'default': get_database_config('default'),
            'external': get_database_config('external', {
                'HOST': '192.168.1.100',
                'PORT': 3306,
                'NAME': 'external_db',
                'USER': 'db_user',
                'PASSWORD': 'db_password',
            })
        }
    """
    # 数据库配置前缀，例如 DB_EXTERNAL_HOST
    prefix = f"DB_{db_name.upper()}"

    config = {
        'ENGINE': os.getenv(f'{prefix}_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv(f'{prefix}_NAME', os.getenv('DB_NAME', 'app_db')),
        'USER': os.getenv(f'{prefix}_USER', os.getenv('DB_USER', 'root')),
        'PASSWORD': os.getenv(f'{prefix}_PASSWORD', os.getenv('DB_PASSWORD', '')),
        'HOST': os.getenv(f'{prefix}_HOST', os.getenv('DB_HOST', 'localhost')),
        'PORT': os.getenv(f'{prefix}_PORT', os.getenv('DB_PORT', '3306')),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }

    # 合并自定义配置
    if custom_config:
        config.update(custom_config)

    return config


# 默认数据库配置
DATABASES = {
    'default': get_database_config('default')
}

# 如果需要连接外部数据库，在这里添加
# 示例：
# DATABASES['external'] = get_database_config('external', {
#     'HOST': '192.168.1.100',
#     'PORT': 3306,
#     'NAME': 'external_db',
#     'USER': 'external_user',
#     'PASSWORD': 'external_password',
# })