"""
Celery 配置文件
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('prison_facial_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 定时任务配置
app.conf.beat_schedule = {
    'reset-daily-stats-every-day': {
        'task': 'apps.users.tasks.reset_daily_stats',
        'schedule': crontab(hour=0, minute=0),  # 每天凌晨 00:00 执行
    },
    # sync-prisoner-data 通过数据库记录管理，不在这里配置
    # 避免 DatabaseScheduler 重启时补执行导致重复同步
}