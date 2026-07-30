"""
一体机人员下发同步服务

把 PrisonerArchive 的罪犯数据通过 WebSocket 下发到在线的一体机设备。
face_template 用照片 URL，设备自己拉取。

触发方式：
  - 手动：HandheldSyncController HTTP 端点 -> threading.Thread
  - 进度查询：HandheldSyncController GET -> get_sync_progress()
"""
import logging
import threading
import time
from datetime import timedelta
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.users.models import Device, DeviceSyncLog, PrisonerArchive

logger = logging.getLogger(__name__)

# 单设备下发批间隔（秒），避免压垮设备
BATCH_INTERVAL_SEC = 0.3

# 发完所有 addUser 后等待设备回执的最长时间（秒）。
# 在此期间 is_running 保持 True，前端持续轮询能看到实时成功数。
ACK_WAIT_TIMEOUT_SEC = 120
ACK_POLL_INTERVAL_SEC = 1

# 本地开发环境档案库 xp 字段是 Windows 路径（如 C:\JGXTDB\...），不是 HTTP 链接，
# 设备无法拉取。部署到公安内网后 xp 会是可访问的 HTTP URL，此 fallback 自动失效。
FALLBACK_PHOTO_URL = 'https://iknow-pic.cdn.bcebos.com/0e2442a7d933c8953b1b43f8c31373f0830200c8'

_lock = threading.Lock()
_progress = {
    'is_running': False,
    'total': 0,
    'sent': 0,
    'device_count': 0,
    'prisoner_count': 0,
    'current_prisoner_no': '',
    'current_prisoner_name': '',
    'message': '空闲',
    'started_at': None,
    'finished_at': None,
    'last_error': '',
}


def get_sync_progress():
    """返回当前同步进度快照。success/fail/pending 从 DeviceSyncLog 实时算。"""
    with _lock:
        base = dict(_progress)
    started_at = base.get('started_at')
    if started_at:
        logs = DeviceSyncLog.objects.filter(synced_at__gte=started_at)
        base['success'] = logs.filter(status='success').count()
        base['fail'] = logs.filter(status='fail').count()
        base['pending'] = logs.filter(status='pending').count()
        base['error'] = logs.filter(status='error').count()
        base['timeout'] = logs.filter(status='timeout').count()
    else:
        base['success'] = 0
        base['fail'] = 0
        base['pending'] = 0
        base['error'] = 0
        base['timeout'] = 0
    return base


def _update_progress(**kwargs):
    with _lock:
        _progress.update(kwargs)


class HandheldSyncService:

    def sync_to_all_devices(self, full=True, device_no=None, progress_callback=None):
        """全量同步所有在线设备（或指定设备）。

        手动触发时始终全量同步档案库所有罪犯。
        调用方（HandheldSyncController.post）负责防重入检查。
        """
        with _lock:
            _progress.update(
                is_running=True,
                total=0,
                sent=0,
                device_count=0,
                prisoner_count=0,
                current_prisoner_no='',
                current_prisoner_name='',
                message='准备同步...',
                started_at=timezone.now(),
                finished_at=None,
                last_error='',
            )

        try:
            self._run_sync(device_no, progress_callback)
        except Exception as e:
            logger.exception('一体机同步异常')
            with _lock:
                _progress.update(
                    is_running=False,
                    message=f'同步异常: {e}',
                    finished_at=timezone.now(),
                    last_error=str(e),
                )

    def _run_sync(self, device_no, progress_callback):
        devices = list(Device.objects.filter(is_online=True))
        if device_no:
            devices = [d for d in devices if d.device_no == device_no]

        if not devices:
            _update_progress(
                is_running=False,
                message='没有在线设备，请先连接一体机',
                finished_at=timezone.now(),
            )
            if progress_callback:
                progress_callback('没有在线设备', total=0, current=0)
            return

        prisoners = list(PrisonerArchive.objects.all())
        if not prisoners:
            _update_progress(
                is_running=False,
                message='档案库为空',
                finished_at=timezone.now(),
            )
            if progress_callback:
                progress_callback('档案库为空', total=0, current=0)
            return

        total = len(devices) * len(prisoners)
        _update_progress(
            total=total,
            device_count=len(devices),
            prisoner_count=len(prisoners),
            message=f'开始同步：{len(devices)} 台设备 × {len(prisoners)} 人 = {total} 条',
        )
        if progress_callback:
            progress_callback('开始同步', total=total, current=0)

        sent = 0
        for device in devices:
            if not device.is_online:
                continue
            for prisoner in prisoners:
                _update_progress(
                    current_prisoner_no=prisoner.prisoner_no,
                    current_prisoner_name=prisoner.prisoner_name or '',
                    message=f'正在下发: {prisoner.prisoner_name or prisoner.prisoner_no} ({prisoner.prisoner_no})',
                    sent=sent,
                )
                self._sync_one(device, prisoner, full=True)
                sent += 1
                if progress_callback and sent % 10 == 0:
                    progress_callback(f'已下发 {sent}/{total}', total=total, current=sent)
                time.sleep(BATCH_INTERVAL_SEC)

        _update_progress(
            sent=sent,
            current_prisoner_no='',
            current_prisoner_name='',
            message=f'下发完成：共 {sent} 条，等待设备回执...',
        )
        if progress_callback:
            progress_callback('下发完成', total=total, current=sent)

        # 等待设备回执，期间 is_running 保持 True，前端能看到实时成功数
        with _lock:
            started_at = _progress['started_at']
        self._wait_for_acks(started_at, total, sent)

        final = get_sync_progress()
        success = final['success']
        fail = final['fail'] + final['error']
        pending = final['pending']
        _update_progress(
            is_running=False,
            current_prisoner_no='',
            current_prisoner_name='',
            message=f'同步结束：成功 {success} 条，失败 {fail} 条，未回执 {pending} 条',
            finished_at=timezone.now(),
        )

    def _wait_for_acks(self, started_at, total, sent):
        """发完 addUser 后等设备回执，期间实时更新进度消息。

        所有 pending 都变成 success/fail/timeout/error，或超时后退出。
        """
        deadline = timezone.now() + timedelta(seconds=ACK_WAIT_TIMEOUT_SEC)
        last_pending = -1
        while timezone.now() < deadline:
            logs = DeviceSyncLog.objects.filter(synced_at__gte=started_at)
            pending = logs.filter(status='pending').count()
            success = logs.filter(status='success').count()
            fail = logs.filter(status='fail').count() + logs.filter(status='error').count()
            if pending == 0:
                _update_progress(
                    message=f'回执完成：成功 {success} 条，失败 {fail} 条',
                )
                return
            if pending != last_pending:
                _update_progress(
                    message=f'等待设备回执... 成功 {success} / 失败 {fail} / 待回执 {pending}',
                )
                last_pending = pending
            time.sleep(ACK_POLL_INTERVAL_SEC)
        # 超时退出
        logs = DeviceSyncLog.objects.filter(synced_at__gte=started_at)
        pending = logs.filter(status='pending').count()
        success = logs.filter(status='success').count()
        fail = logs.filter(status='fail').count() + logs.filter(status='error').count()
        _update_progress(
            message=f'回执超时({ACK_WAIT_TIMEOUT_SEC}s)：成功 {success} 条，失败 {fail} 条，未回执 {pending} 条',
        )

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
        """从 media_info 取第一张照片 URL，normalize 后返回。

        如果 xp 不是 HTTP 链接（本地开发是 Windows 路径），用 FALLBACK_PHOTO_URL 替代。
        """
        from apps.users.controllers.archive_controller import _normalize_photo_url
        raw = None
        if prisoner.media_info:
            for item in prisoner.media_info:
                if isinstance(item, dict) and item.get('xp'):
                    raw = item['xp']
                    break
        if not raw:
            return None
        url = _normalize_photo_url(raw)
        if url.startswith('http://') or url.startswith('https://'):
            return url
        return FALLBACK_PHOTO_URL

    def _convert_id_valid(self, sentence_end):
        """yyyy.MM.dd -> yyyy-MM-dd，空值返回空串"""
        if not sentence_end:
            return ''
        return sentence_end.replace('.', '-')
