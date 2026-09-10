"""
清理脚本：清空所有出入监记录、统计数据、本地生成的视频和图片

用法：python manage.py cleanup_data
"""

import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.users.models import ExitEntryRecord, DailyStatistics, HistoryStatistics


class Command(BaseCommand):
    help = '清空所有出入监记录、统计数据及本地媒体文件'

    def handle(self, *args, **options):
        record_count = ExitEntryRecord.objects.count()
        daily_count = DailyStatistics.objects.count()
        history_count = HistoryStatistics.objects.count()

        media_root = settings.MEDIA_ROOT
        dirs = {
            'faces': os.path.join(media_root, 'faces'),
            'videos': os.path.join(media_root, 'videos'),
            'attachments': os.path.join(media_root, 'attachments'),
        }

        # 清理数据库
        ExitEntryRecord.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  [DB] 已删除 {record_count} 条出入监记录'))

        DailyStatistics.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  [DB] 已删除 {daily_count} 条每日统计'))

        HistoryStatistics.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  [DB] 已删除 {history_count} 条历史统计'))

        # 清理媒体文件
        for name, path in dirs.items():
            if os.path.exists(path):
                count = 0
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        count += 1
                self.stdout.write(self.style.SUCCESS(f'  [文件] 已清理 {name}/ ({count} 个)'))

        self.stdout.write(self.style.SUCCESS('\n清理完成。'))
