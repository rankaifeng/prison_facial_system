"""
Celery 配置文件
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('prison_facial_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 定时任务通过 django_celery_beat 的数据库表管理（DatabaseScheduler）
# 在 deploy-package/install.sh 部署时通过 manage.py shell 注册：
#   - 每日同步罪犯数据 (apps.users.tasks.sync_prisoner_data_task)  00:05
#   - 每日统计重置     (apps.users.tasks.reset_daily_stats)        00:00
# 不在 app.conf.beat_schedule 静态配置，避免 DatabaseScheduler 重启时补执行导致重复