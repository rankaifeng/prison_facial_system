import json
import asyncio
import uuid
import logging
from django.utils import timezone as dt_timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

# 存储 Daphne 事件循环引用，供后台线程调度广播
_event_loop = None


def get_event_loop():
    return _event_loop


class DoorEventConsumer(AsyncWebsocketConsumer):
    group_name = 'door_events'

    async def connect(self):
        global _event_loop
        _event_loop = asyncio.get_running_loop()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def door_event(self, event):
        await self.send(text_data=json.dumps(event['data'], ensure_ascii=False))


class DeviceConsumer(AsyncWebsocketConsumer):
    """一体机设备 WebSocket 连接 - 处理 declare/heartbeat/addUserRet"""

    async def connect(self):
        client = self.scope.get('client')
        client_ip = f"{client[0]}:{client[1]}" if client else '?'
        logger.info('[设备] WS 连接 来自 %s', client_ip)
        await self.accept()

    async def disconnect(self, close_code):
        device_no = getattr(self, 'device_no', None)
        logger.info('[设备] WS 断开 device_no=%s code=%s', device_no, close_code)
        if device_no:
            await self.channel_layer.group_discard(f'device_{device_no}', self.channel_name)
            await database_sync_to_async(self._mark_offline)(device_no)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning('[设备] 非 JSON 消息: %s', text_data[:200])
            return
        cmd = data.get('cmd', '')
        logger.info('[设备] 收到 cmd=%s data=%s', cmd, str(data)[:300])

        if cmd in ('declare', 'register'):
            await self._handle_declare(data)
        elif cmd in ('heartbeat', 'ping'):
            await self._handle_heartbeat(data)
        elif cmd == 'to_client':
            await self._handle_to_client(data)
        else:
            logger.info('[设备] 未处理的 cmd=%s', cmd)

    async def _handle_declare(self, data):
        device_no = data.get('sn') or data.get('device_no') or data.get('deviceNo') or ''
        if not device_no:
            logger.warning('[设备] declare 缺少 sn/device_no: %s', data)
            return
        self.device_no = device_no
        await self.channel_layer.group_add(f'device_{device_no}', self.channel_name)

        client_id = f'server_{uuid.uuid4().hex[:12]}'
        await database_sync_to_async(self._upsert_device)(device_no, client_id, data)

        ack = {
            'cmd': 'declare_ack',
            'client_id': client_id,
            'sn': device_no,
            'code': 0,
            'msg': '声明成功',
        }
        await self.send(text_data=json.dumps(ack, ensure_ascii=False))
        logger.info('[设备] declare_ack 已发送 sn=%s client_id=%s', device_no, client_id)

    async def _handle_heartbeat(self, data):
        device_no = getattr(self, 'device_no', None) or data.get('sn') or data.get('device_no') or ''
        if device_no:
            await database_sync_to_async(self._touch_device)(device_no)
        await self.send(text_data=json.dumps({
            'cmd': 'heartbeat_ack',
            'code': 0,
            'msg': 'ok',
        }, ensure_ascii=False))

    async def _handle_to_client(self, data):
        inner = data.get('data', {}) or {}
        inner_cmd = inner.get('cmd', '')
        if inner_cmd == 'addUserRet':
            device_no = getattr(self, 'device_no', None)
            user_id = inner.get('user_id', '')
            code = inner.get('code', '')
            msg = inner.get('msg', '')
            logger.info('[设备] addUserRet sn=%s user_id=%s code=%s msg=%s', device_no, user_id, code, msg)
            await database_sync_to_async(self._record_sync_result)(
                device_no, user_id, code, msg)

    async def send_command(self, event):
        """由 channel_layer.group_send({'type':'send_command','payload':...}) 触发，把命令转发给设备"""
        await self.send(text_data=json.dumps(event['payload'], ensure_ascii=False))

    # ===== 同步 DB 辅助方法（被 database_sync_to_async 包装调用） =====

    def _upsert_device(self, device_no, client_id, data):
        from apps.users.models import Device
        defaults = {
            'is_online': True,
            'client_id': client_id,
            'last_seen_at': dt_timezone.now(),
        }
        if data.get('name'):
            defaults['name'] = data['name']
        if data.get('prison_area'):
            defaults['prison_area'] = data['prison_area']
        Device.objects.update_or_create(device_no=device_no, defaults=defaults)

    def _touch_device(self, device_no):
        from apps.users.models import Device
        from django.utils import timezone
        Device.objects.filter(device_no=device_no).update(
            last_seen_at=timezone.now(), is_online=True)

    def _mark_offline(self, device_no):
        from apps.users.models import Device
        from django.utils import timezone
        Device.objects.filter(device_no=device_no).update(
            is_online=False, last_seen_at=timezone.now())

    def _record_sync_result(self, device_no, user_id, code, msg):
        from apps.users.models import Device, DeviceSyncLog, PrisonerArchive
        from django.utils import timezone
        if not device_no or not user_id:
            return
        try:
            device = Device.objects.get(device_no=device_no)
        except Device.DoesNotExist:
            return
        log = DeviceSyncLog.objects.filter(
            device=device, prisoner_no=user_id, status='pending'
        ).order_by('-synced_at').first()
        if not log:
            return
        if code == 0 or code == '0':
            log.status = 'success'
            PrisonerArchive.objects.filter(prisoner_no=user_id).update(
                last_synced_to_terminal_photo_url=log.photo_url,
                last_synced_to_terminal_at=timezone.now(),
            )
        else:
            log.status = 'fail'
        log.error_code = str(code) if code != 0 and code != '0' else ''
        log.error_msg = msg or ''
        log.save(update_fields=['status', 'error_code', 'error_msg'])
