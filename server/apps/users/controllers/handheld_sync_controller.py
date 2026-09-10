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
    request_cancel,
    is_cancelled,
    is_sync_thread_active,
    _update_progress,
)

logger = logging.getLogger(__name__)


class HandheldSyncController(APIView):
    """触发手持终端同步 + 查询进度

    POST /user_manage/handheld-sync/trigger/   触发全量同步（后台线程）
    GET  /user_manage/handheld-sync/progress/  返回当前进度
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if is_sync_thread_active() and not is_cancelled():
            return Response({'code': 0, 'msg': '已有同步任务在运行', 'data': {'is_running': True}})

        _update_progress(is_running=True, phase='idle', message='准备同步...',
                         started_at=timezone.now(), finished_at=None, last_error='')

        thread = threading.Thread(target=HandheldSyncService().sync_all, daemon=True)
        thread.start()

        return Response({'code': 1, 'msg': '已触发同步', 'data': {}})


class HandheldSyncProgressController(APIView):
    """查询手持终端同步进度 - GET /user_manage/handheld-sync/progress/"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        progress = get_sync_progress()
        if progress.get('started_at'):
            progress['started_at'] = progress['started_at'].isoformat()
        if progress.get('finished_at'):
            progress['finished_at'] = progress['finished_at'].isoformat()
        return Response({'code': 1, 'data': progress})


class HandheldSyncCancelController(APIView):
    """取消手持终端同步 - POST /user_manage/handheld-sync/cancel/"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current = get_sync_progress()
        if not current.get('is_running'):
            return Response({'code': 1, 'msg': '没有正在进行的同步'})
        request_cancel()
        # 立即标记为非运行状态，前端停止轮询
        _update_progress(is_running=False, phase='done', message='同步已取消',
                         finished_at=timezone.now())
        return Response({'code': 1, 'msg': '已取消同步'})
