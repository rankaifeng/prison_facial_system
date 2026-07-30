import logging
import threading
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.services.handheld_sync_service import (
    HandheldSyncService,
    get_sync_progress,
    _update_progress,
)
from apps.users.models import Device

logger = logging.getLogger(__name__)


class HandheldSyncController(APIView):
    """手动触发一体机同步 + 查询进度

    POST /user_manage/handheld-sync/trigger/   触发全量同步（后台线程跑）
    GET  /user_manage/handheld-sync/progress/  返回当前进度
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_no = request.data.get('device_no') or None

        # 防重入：已有同步在跑就直接拒绝
        current = get_sync_progress()
        if current.get('is_running'):
            return Response({
                'code': 0,
                'msg': '已有同步任务在运行',
                'data': {'is_running': True},
            })

        # 同步标记 is_running，避免前端触发后立即查询时还没置位导致轮询不启动
        _update_progress(
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

        def _progress(msg, total, current):
            logger.info('一体机同步: %s', msg)

        thread = threading.Thread(
            target=HandheldSyncService().sync_to_all_devices,
            kwargs={'full': True, 'device_no': device_no, 'progress_callback': _progress},
            daemon=True,
        )
        thread.start()

        return Response({
            'code': 1,
            'msg': '已触发全量同步',
            'data': {'device_no': device_no},
        })


class HandheldSyncProgressController(APIView):
    """查询一体机同步进度 - GET /user_manage/handheld-sync/progress/"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        progress = get_sync_progress()
        devices = list(Device.objects.all().values('device_no', 'name', 'is_online', 'last_seen_at'))
        for d in devices:
            if d.get('last_seen_at'):
                d['last_seen_at'] = d['last_seen_at'].isoformat()
        progress['devices'] = devices
        if progress.get('started_at'):
            progress['started_at'] = progress['started_at'].isoformat()
        if progress.get('finished_at'):
            progress['finished_at'] = progress['finished_at'].isoformat()
        return Response({'code': 1, 'data': progress})
