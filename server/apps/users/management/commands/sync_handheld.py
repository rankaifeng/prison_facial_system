"""
同步罪犯数据到一体机设备

用法:
  python manage.py sync_handheld                    # 增量同步到所有在线设备
  python manage.py sync_handheld --full             # 全量同步
  python manage.py sync_handheld --device TEST001   # 只同步到指定设备
"""
from django.core.management.base import BaseCommand
from apps.users.services.handheld_sync_service import HandheldSyncService


def flush_print(msg=''):
    print(msg, flush=True)


class Command(BaseCommand):
    help = '同步罪犯数据到一体机设备'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full', action='store_true', default=False,
            help='全量同步（默认增量）',
        )
        parser.add_argument(
            '--device', type=str, default='',
            help='只同步到指定设备编号',
        )

    def handle(self, *args, **options):
        full = options['full']
        device_no = options['device'] or None

        flush_print('\n=== 同步罪犯数据到一体机 ===')
        flush_print(f'模式: {"全量" if full else "增量"}')
        if device_no:
            flush_print(f'目标设备: {device_no}')
        flush_print('')

        def progress(msg, total, current):
            flush_print(f'  {msg}')

        service = HandheldSyncService()
        service.sync_to_all_devices(
            full=full, device_no=device_no, progress_callback=progress)

        flush_print('\n=== 同步结束 ===')
