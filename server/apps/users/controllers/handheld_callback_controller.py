import os
import base64
import logging
import urllib.parse
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.users.models import PrisonerArchive, FaceRecognitionRecord
from apps.users.controllers.archive_controller import _normalize_photo_url

logger = logging.getLogger(__name__)


class HandheldCallbackController(APIView):
    """新手持终端识别回调接口

    设备识别成功后 POST 到 /api/v1/handheld-callback/
    参数: pass, deviceKey, personId, time, type, imgBase64, data, ip, searchScore, livenessScore
    无认证（设备直接调用）
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        person_id = request.POST.get('personId', '') or request.data.get('personId', '')

        # 陌生人和无效ID直接跳过，不打日志
        if not person_id or person_id.upper() in ('STRANGERBABY', 'STRANGER', 'UNKNOWN', ''):
            return Response({'success': True, 'msg': 'ok'})

        device_key = request.POST.get('deviceKey', '') or request.data.get('deviceKey', '')
        img_base64 = request.POST.get('imgBase64', '') or request.data.get('imgBase64', '')
        recog_time = request.POST.get('time', '') or request.data.get('time', '')
        recog_type = request.POST.get('type', '') or request.data.get('type', '')
        ip = request.POST.get('ip', '') or request.data.get('ip', '')
        score = request.POST.get('searchScore', '') or request.data.get('searchScore', '')
        liveness_score = request.POST.get('livenessScore', '') or request.data.get('livenessScore', '')

        logger.info(f'[手持终端回调] ========== 收到识别结果 ==========')
        logger.info(f'[手持终端回调] personId={person_id}')
        logger.info(f'[手持终端回调] deviceKey={device_key}')
        logger.info(f'[手持终端回调] type={recog_type}')
        logger.info(f'[手持终端回调] searchScore={score}')
        logger.info(f'[手持终端回调] livenessScore={liveness_score}')
        logger.info(f'[手持终端回调] time={recog_time}')
        logger.info(f'[手持终端回调] ip={ip}')
        logger.info(f'[手持终端回调] imgBase64长度={len(img_base64)} 字符')

        try:
            self._handle(person_id, device_key, img_base64, recog_time, request)
        except Exception as e:
            logger.exception(f'[手持终端回调] 处理异常: {e}')

        logger.info(f'[手持终端回调] ========== 回调处理完成 ==========')
        return Response({'success': True, 'msg': 'ok'})

    def _handle(self, person_id, device_key, img_base64, recog_time, request):
        device_no = device_key or 'handheld'
        recognized_at = self._parse_time(recog_time)

        # 去重：同设备、同人、同时间的记录已存在则跳过（设备会重发旧回调）
        if recognized_at and FaceRecognitionRecord.objects.filter(
                device_no=device_no, user_id=person_id, recognized_at=recognized_at).exists():
            logger.info(f'[手持终端回调] 重复回调，跳过: personId={person_id}, time={recog_time}')
            return

        logger.info(f'[手持终端回调] 开始处理 personId={person_id}')

        captured_url = self._save_photo(img_base64, person_id)
        if captured_url:
            captured_url = request.build_absolute_uri(captured_url)
        logger.info(f'[手持终端回调] 抓拍照片: {captured_url or "无"}')

        prisoner = None
        archive_photo_url = ''
        if person_id:
            try:
                prisoner = PrisonerArchive.objects.get(prisoner_no=person_id)
                archive_photo_url = self._get_archive_photo_url(prisoner)
                logger.info(f'[手持终端回调] 命中档案: {person_id} -> {prisoner.prisoner_name}, 档案照片: {archive_photo_url or "无"}')
            except PrisonerArchive.DoesNotExist:
                logger.warning(f'[手持终端回调] 未命中档案: {person_id}')

        logger.info(f'[手持终端回调] 识别时间: {recognized_at}')

        record = FaceRecognitionRecord.objects.create(
            device_no=device_no,
            user_id=person_id,
            prisoner=prisoner,
            captured_photo_url=captured_url,
            recognized_at=recognized_at,
            raw_data={'personId': person_id, 'deviceKey': device_key, 'time': recog_time},
        )
        logger.info(f'[手持终端回调] 识别记录已保存 id={record.id}')

        # 前端需要 base64 数据来显示图片，直接用设备发来的原始数据
        raw_base64 = self._clean_base64(img_base64)
        logger.info(f'[手持终端回调] base64清理后长度: {len(raw_base64)} 字符')
        self._push_to_frontend(person_id, prisoner, raw_base64, archive_photo_url, device_key)

    def _clean_base64(self, img_base64):
        if not img_base64:
            return ''
        if '%' in img_base64:
            img_base64 = urllib.parse.unquote(img_base64)
        if img_base64.startswith('data:') and ',' in img_base64:
            img_base64 = img_base64.split(',', 1)[1]
        return img_base64.replace('\n', '').replace('\r', '').replace(' ', '')

    def _save_photo(self, img_base64, person_id):
        if not img_base64:
            return ''
        try:
            if '%' in img_base64:
                img_base64 = urllib.parse.unquote(img_base64)
            if img_base64.startswith('data:') and ',' in img_base64:
                img_base64 = img_base64.split(',', 1)[1]
            img_base64 = img_base64.replace('\n', '').replace('\r', '').replace(' ', '')
            missing = len(img_base64) % 4
            if missing:
                img_base64 += '=' * (4 - missing)
            photo_bytes = base64.b64decode(img_base64)
        except Exception as e:
            logger.warning(f'[手持终端回调] base64解码失败: {e}')
            return ''

        safe_id = (person_id or 'unknown').replace('/', '_').replace('\\', '_')
        ts = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{safe_id}_{ts}.jpg'
        save_dir = os.path.join(settings.MEDIA_ROOT, 'device_photos')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        try:
            with open(save_path, 'wb') as f:
                f.write(photo_bytes)
        except Exception as e:
            logger.warning(f'[手持终端回调] 保存照片失败: {e}')
            return ''

        return f'/media/device_photos/{filename}'

    def _get_archive_photo_url(self, prisoner):
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
            ts = int(recog_time)
            if ts > 1e12:
                ts = ts / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            pass
        try:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S'):
                try:
                    return datetime.strptime(recog_time, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        except Exception:
            pass
        return None

    def _push_to_frontend(self, person_id, prisoner, raw_base64, archive_photo_url, device_key):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning(f'[手持终端回调] channel_layer不可用，无法推送到前端')
            return
        payload = {
            'type': 'prisoner_face',
            'source': 'handheld',
            'user_id': person_id,
            'prisoner_no': prisoner.prisoner_no if prisoner else person_id,
            'prisoner_name': prisoner.prisoner_name if prisoner else '',
            'image_base64': raw_base64,
            'archive_image_base64': archive_photo_url,
            'device_no': device_key or 'handheld',
        }
        logger.info(f'[手持终端回调] 推送前端: personId={person_id}, prisoner_name={payload["prisoner_name"]}, '
                     f'抓拍base64长度={len(raw_base64)}, 档案照片={archive_photo_url or "无"}')
        try:
            async_to_sync(channel_layer.group_send)(
                'door_events',
                {'type': 'door_event', 'data': payload}
            )
            logger.info(f'[手持终端回调] 推前端成功 personId={person_id}')
        except Exception as e:
            logger.exception(f'[手持终端回调] 推前端失败: {e}')
