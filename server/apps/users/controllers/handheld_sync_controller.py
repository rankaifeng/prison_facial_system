import logging
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.services.handheld_sync_service import HandheldSyncService

logger = logging.getLogger(__name__)


class HandheldSyncController(APIView):
    """手动触发一体机同步 - POST /user_manage/handheld-sync/trigger/

    后台线程跑同步，立即返回"已触发"。同步进度不回传（初版）。
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        full = bool(request.data.get('full', False))
        device_no = request.data.get('device_no') or None

        def _progress(msg, total, current):
            logger.info('一体机同步: %s', msg)

        thread = threading.Thread(
            target=HandheldSyncService().sync_to_all_devices,
            kwargs={'full': full, 'device_no': device_no, 'progress_callback': _progress},
            daemon=True,
        )
        thread.start()

        return Response({
            'code': 1,
            'msg': f'已触发{"全量" if full else "增量"}同步',
            'data': {'full': full, 'device_no': device_no},
        })
