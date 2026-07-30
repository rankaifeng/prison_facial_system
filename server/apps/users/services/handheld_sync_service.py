"""
一体机人员下发同步服务

把 PrisonerArchive 的罪犯数据通过 WebSocket 下发到在线的一体机设备。
face_template 直接用照片 URL（设备自己拉取），不用 base64。

触发方式：
  - 手动：HandheldSyncController HTTP 端点 -> threading.Thread
  - 定时：Celery sync_to_handheld_task -> HTTP 调 Daphne 端点
"""
import logging
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.users.models import Device, DeviceSyncLog, PrisonerArchive
from apps.users.controllers.archive_controller import _normalize_photo_url

logger = logging.getLogger(__name__)

# 单设备下发批间隔（秒），避免压垮设备
BATCH_INTERVAL_SEC = 0.3


class HandheldSyncService:

    def sync_to_all_devices(self, full=False, device_no=None, progress_callback=None):
        """同步所有在线设备（或指定设备）"""
        devices = Device.objects.filter(is_online=True)
        if device_no:
            devices = devices.filter(device_no=device_no)

        if not devices:
            if progress_callback:
                progress_callback('没有在线设备，跳过', total=0, current=0)
            logger.warning('一体机同步：没有在线设备')
            return

        prisoners = self._select_prisoners_to_sync(full)
        if not prisoners:
            if progress_callback:
                progress_callback('没有需要同步的罪犯', total=0, current=0)
            logger.warning('一体机同步：没有需要同步的罪犯')
            return

        sync_type = 'full' if full else 'incremental'
        total = len(devices) * len(prisoners)
        if progress_callback:
            progress_callback(
                f'开始{sync_type}同步：{len(devices)} 台设备 × {len(prisoners)} 人 = {total} 条',
                total=total, current=0)

        current = 0
        for device in devices:
            if not device.is_online:
                continue
            for prisoner in prisoners:
                self._sync_one(device, prisoner, full)
                current += 1
                if progress_callback and current % 20 == 0:
                    progress_callback(
                        f'已下发 {current}/{total}（设备 {device.device_no}）',
                        total=total, current=current)
                time.sleep(BATCH_INTERVAL_SEC)

        if progress_callback:
            progress_callback(f'同步完成，共下发 {current} 条', total=total, current=current)

    def _sync_one(self, device, prisoner, full):
        photo_url = self._get_photo_url(prisoner)
        if not photo_url:
            DeviceSyncLog.objects.create(
                device=device,
                prisoner_no=prisoner.prisoner_no,
                sync_type='full' if full else 'incremental',
                status='error',
                error_msg='档案无照片',
            )
            return
        self._send_add_user(device, prisoner, photo_url, full)

    def _send_add_user(self, device, prisoner, photo_url, full):
        log = DeviceSyncLog.objects.create(
            device=device,
            prisoner_no=prisoner.prisoner_no,
            sync_type='full' if full else 'incremental',
            status='pending',
            photo_url=photo_url,
        )
        message = {
            'cmd': 'to_device',
            'from': 'server',
            'to': device.device_no,
            'extra': str(log.id),
            'data': {
                'cmd': 'addUser',
                'user_id': prisoner.prisoner_no,
                'name': prisoner.prisoner_name or '',
                'id_card': prisoner.id_card or '',
                'face_template': photo_url,
                'id_valid': self._convert_id_valid(prisoner.sentence_end),
                'user_type': 0,
                'mode': '0',
            },
        }
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                log.status = 'error'
                log.error_msg = 'channel layer 不可用'
                log.save(update_fields=['status', 'error_msg'])
                return
            async_to_sync(channel_layer.group_send)(
                f'device_{device.device_no}',
                {'type': 'send_command', 'payload': message}
            )
        except Exception as e:
            logger.exception('下发 addUser 失败 device=%s prisoner=%s',
                             device.device_no, prisoner.prisoner_no)
            log.status = 'error'
            log.error_msg = str(e)[:500]
            log.save(update_fields=['status', 'error_msg'])

    def _get_photo_url(self, prisoner):
        """从 media_info 取第一张照片 URL，normalize 后返回"""
        if not prisoner.media_info:
            return None
        for item in prisoner.media_info:
            if isinstance(item, dict) and item.get('xp'):
                return _normalize_photo_url(item['xp'])
        return None

    def _convert_id_valid(self, sentence_end):
        """yyyy.MM.dd -> yyyy-MM-dd，空值返回空串"""
        if not sentence_end:
            return ''
        return sentence_end.replace('.', '-')

    def _select_prisoners_to_sync(self, full):
        """全量：所有罪犯；增量：照片 URL 变化或从未同步的"""
        all_prisoners = list(PrisonerArchive.objects.all())
        if full:
            return all_prisoners
        need_sync = []
        for p in all_prisoners:
            current_url = self._get_photo_url(p) or ''
            if current_url != (p.last_synced_to_terminal_photo_url or ''):
                need_sync.append(p)
        return need_sync
