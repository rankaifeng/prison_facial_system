import pymysql
pymysql.install_as_MySQLdb()

# 导入 Celery
from .celery import app as celery_app
__all__ = ('celery_app',)
