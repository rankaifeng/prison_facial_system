from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication


class SyncStartController(APIView):
    """启动手动同步任务"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.users.tasks import sync_prisoner_data_with_progress
        task = sync_prisoner_data_with_progress.delay()
        return Response({'code': 1, 'msg': '同步任务已启动', 'data': {'task_id': task.id}})


class SyncStatusController(APIView):
    """查询同步任务状态"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from celery.result import AsyncResult
        from apps.users.tasks import sync_prisoner_data_with_progress

        task_id = request.query_params.get('task_id', '').strip()
        if not task_id:
            return Response({'code': 0, 'msg': '缺少 task_id', 'data': None})

        result = AsyncResult(task_id, app=sync_prisoner_data_with_progress.app)

        if result.state == 'PENDING':
            data = {'state': 'PENDING', 'current': 0, 'total': 0, 'step': 'waiting',
                    'message': '等待中...', 'percent': 0}
        elif result.state == 'PROGRESS':
            info = result.info or {}
            data = {'state': 'PROGRESS', **info}
        elif result.state == 'SUCCESS':
            info = result.info or {}
            data = {'state': 'SUCCESS', 'current': 100, 'total': 100, 'step': 'done',
                    'message': info.get('message', '同步完成'), 'percent': 100}
        else:
            info = result.info or {}
            data = {'state': 'FAILURE', 'current': 0, 'total': 0, 'step': 'error',
                    'message': str(info) if info else '同步失败', 'percent': 0}

        return Response({'code': 1, 'msg': 'success', 'data': data})
