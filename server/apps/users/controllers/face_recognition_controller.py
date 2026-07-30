import os
import json
import base64
import logging
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
        try:
            data = json.loads(request.body)
        except Exception:
            logger.warning('record/face JSON 解析失败')
            return Response({'Result': 0, 'Msg': ''})

        sn = data.get('sn', '')
        logs = data.get('logs', []) or []
        client_ip = request.META.get('REMOTE_ADDR', '?')
        logger.info('[识别回调] 收到 来自=%s sn=%s 记录数=%d', client_ip, sn, len(logs))

        for log_entry in logs:
            try:
                self._handle_one(log_entry, sn)
            except Exception as e:
                logger.exception('处理识别记录异常: %s', e)

        return Response({'Result': 0, 'Msg': ''})

    def _handle_one(self, log_entry, sn):
        user_id = log_entry.get('user_id', '') or ''
        photo_b64 = log_entry.get('photo', '') or ''
        recog_time = log_entry.get('recog_time', '') or ''

        logger.info('[识别回调] 处理 sn=%s user_id=%s recog_time=%s photo_len=%d',
                    sn, user_id, recog_time, len(photo_b64))

        captured_url = self._save_photo(photo_b64, user_id, recog_time)

        prisoner = None
        archive_photo_url = ''
        if user_id:
            try:
                prisoner = PrisonerArchive.objects.get(prisoner_no=user_id)
                archive_photo_url = self._get_archive_photo_url(prisoner)
                logger.info('[识别回调] 命中档案 user_id=%s prisoner=%s archive_url=%s',
                            user_id, prisoner.prisoner_name, archive_photo_url)
            except PrisonerArchive.DoesNotExist:
                logger.warning('[识别回调] 未命中档案 user_id=%s', user_id)

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
        """base64 解码后存到 media/device_photos/，返回可访问 URL"""
        if not photo_b64:
            return ''
        try:
            if ',' in photo_b64 and photo_b64.startswith('data:'):
                photo_b64 = photo_b64.split(',', 1)[1]
            photo_bytes = base64.b64decode(photo_b64)
        except Exception as e:
            logger.warning('base64 解码失败: %s', e)
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
            logger.exception('保存现场照失败: %s', e)
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
            logger.warning('[识别回调] channel_layer 不可用，无法推前端')
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
            logger.info('[识别回调] 已推前端 user_id=%s prisoner_no=%s captured_url=%s',
                        user_id, payload['prisoner_no'], captured_url)
        except Exception as e:
            logger.exception('推送识别事件到前端失败: %s', e)
