"""
设置 Celery Beat 定时任务

用法: python manage.py setup_periodic_tasks
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = '创建/更新 Celery Beat 定时任务'

    def handle(self, *args, **options):
        schedule_data, _ = CrontabSchedule.objects.get_or_create(
            minute='5', hour='0', day_of_week='*', day_of_month='*', month_of_year='*'
        )
        schedule_dahua, _ = CrontabSchedule.objects.get_or_create(
            minute='30', hour='0', day_of_week='*', day_of_month='*', month_of_year='*'
        )

        tasks = [
            {
                'name': '每日同步罪犯数据',
                'task': 'apps.users.tasks.sync_prisoner_data_task',
                'crontab': schedule_data,
                'time': '00:05',
            },
            {
                'name': '每日同步到大华门禁',
                'task': 'apps.users.tasks.sync_dahua_task',
                'crontab': schedule_dahua,
                'time': '00:30',
            },
        ]

        for t in tasks:
            obj, created = PeriodicTask.objects.update_or_create(
                name=t['name'],
                defaults={
                    'crontab': t['crontab'],
                    'task': t['task'],
                    'args': json.dumps([]),
                    'enabled': True,
                }
            )
            status = '创建' if created else '更新'
            self.stdout.write(f'  {status}: {t["name"]} ({t["time"]}) -> {t["task"]}')

        self.stdout.write(self.style.SUCCESS('定时任务设置完成：档案同步 00:05，大华同步 00:30'))
