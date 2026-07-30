import os
import json
import base64
import logging
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.users.models import PrisonerArchive, FaceRecognitionRecord
from apps.users.controllers.archive_controller import _normalize_photo_url

logger = logging.getLogger(__name__)


class FaceRecognitionController(APIView):
    """一体机人脸识别记录上报接口

    设备识别到人脸后 POST 到 /api/v1/record/face
    无认证（设备不带 JWT），始终返回 Result=0 让设备删本地记录
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """设备识别记录上报 - POST /api/v1/record/face

        格式跟 test/ws_test_server.py 一致：
        {"sn":"SC9823","logs":[{"user_id":"xxx","user_name":"xxx","recog_time":"xxx","photo":"<base64>"}]}
        始终返回 Result=0，设备收到后才会删除本地记录。
        """
        try:
            data = json.loads(request.body)
        except Exception:
            print('[识别回调] JSON 解析失败', flush=True)
            return Response({'Result': 0, 'Msg': ''})

        sn = data.get('sn', '')
        logs = data.get('logs', []) or []
        client_ip = request.META.get('REMOTE_ADDR', '?')
        print(f'[识别回调] 收到 来自={client_ip} sn={sn} 记录数={len(logs)}', flush=True)

        for log_entry in logs:
            try:
                self._handle_one(log_entry, sn)
            except Exception as e:
                print(f'[识别回调] 处理异常: {e}', flush=True)

        return Response({'Result': 0, 'Msg': ''})

    def _handle_one(self, log_entry, sn):
        user_id = log_entry.get('user_id', '') or ''
        user_name = log_entry.get('user_name', '') or ''
        photo_b64 = log_entry.get('photo', '') or ''
        recog_time = log_entry.get('recog_time', '') or ''

        print(f'[识别回调] 处理 sn={sn} user_id={user_id} user_name={user_name} recog_time={recog_time} photo_len={len(photo_b64)}', flush=True)

        captured_url = self._save_photo(photo_b64, user_id, recog_time)

        prisoner = None
        archive_photo_url = ''
        if user_id:
            try:
                prisoner = PrisonerArchive.objects.get(prisoner_no=user_id)
                archive_photo_url = self._get_archive_photo_url(prisoner)
                print(f'[识别回调] 命中档案 user_id={user_id} prisoner={prisoner.prisoner_name} archive_url={archive_photo_url}', flush=True)
            except PrisonerArchive.DoesNotExist:
                print(f'[识别回调] 未命中档案 user_id={user_id}', flush=True)

        recognized_at = self._parse_time(recog_time)
        FaceRecognitionRecord.objects.create(
            device_no=sn,
            user_id=user_id,
            prisoner=prisoner,
            captured_photo_url=captured_url,
            recognized_at=recognized_at,
            raw_data=log_entry,
        )

        self._push_to_frontend(sn, user_id, prisoner, captured_url, archive_photo_url)

    def _save_photo(self, photo_b64, user_id, recog_time):
        """base64 解码后存到 media/device_photos/，返回可访问 URL

        设备发来的 photo 是 URL 编码的 data URI：
        data%3Aimage%2Fjpeg%3Bbase64%2C%2F9j%2F...
        需要先 URL 解码，再去掉 data:image/jpeg;base64, 前缀，再 base64 解码。
        """
        if not photo_b64:
            return ''
        try:
            # 1. URL 解码（设备会 urlencode 整个 data URI）
            if '%' in photo_b64:
                photo_b64 = urllib.parse.unquote(photo_b64)
            # 2. 去掉 data:image/jpeg;base64, 前缀
            if photo_b64.startswith('data:') and ',' in photo_b64:
                photo_b64 = photo_b64.split(',', 1)[1]
            # 3. 清理 base64 中的换行和空白
            photo_b64 = photo_b64.replace('\n', '').replace('\r', '').replace(' ', '')
            # 4. 补齐 padding
            missing = len(photo_b64) % 4
            if missing:
                photo_b64 += '=' * (4 - missing)
            photo_bytes = base64.b64decode(photo_b64)
        except Exception as e:
            print(f'[识别回调] base64 解码失败: {e}', flush=True)
            return ''

        safe_user = (user_id or 'unknown').replace('/', '_').replace('\\', '_')
        ts = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{safe_user}_{ts}.jpg'
        save_dir = os.path.join(settings.MEDIA_ROOT, 'device_photos')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        try:
            with open(save_path, 'wb') as f:
                f.write(photo_bytes)
        except Exception as e:
            print(f'[识别回调] 保存现场照失败: {e}', flush=True)
            return ''

        return f'/media/device_photos/{filename}'

    def _get_archive_photo_url(self, prisoner):
        """从 media_info 取第一张照片 URL，normalize 后返回"""
        if not prisoner.media_info:
            return ''
        for item in prisoner.media_info:
            xp = item.get('xp') if isinstance(item, dict) else None
            if xp:
                return _normalize_photo_url(xp)
        return ''

    def _parse_time(self, recog_time):
        if not recog_time:
            return None
        try:
            dt = parse_datetime(recog_time)
            if dt:
                return dt
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y%m%d%H%M%S'):
                try:
                    return datetime.strptime(recog_time, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    def _push_to_frontend(self, sn, user_id, prisoner, captured_url, archive_photo_url):
        """通过 door_events group 推到前端，复用 prisoner_face 事件类型"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            print('[识别回调] channel_layer 不可用，无法推前端', flush=True)
            return
        payload = {
            'type': 'prisoner_face',
            'source': 'handheld',
            'user_id': user_id,
            'prisoner_no': prisoner.prisoner_no if prisoner else '',
            'prisoner_name': prisoner.prisoner_name if prisoner else '',
            'image_base64': captured_url,
            'archive_image_base64': archive_photo_url,
            'device_no': sn,
        }
        try:
            async_to_sync(channel_layer.group_send)(
                'door_events',
                {'type': 'door_event', 'data': payload}
            )
            print(f'[识别回调] 已推前端 user_id={user_id} prisoner_no={payload["prisoner_no"]} captured_url={captured_url}', flush=True)
        except Exception as e:
            print(f'[识别回调] 推前端失败: {e}', flush=True)
