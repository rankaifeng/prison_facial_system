from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.services import RecordService


class PrisonMessagesController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = max(1, int(request.query_params.get('limit', 20)))
        except (TypeError, ValueError):
            page_size = 20

        # 非管理员只能看本监区的消息（多监区为逗号分隔）；未配置监区则无数据
        prison_area = None
        if request.user.role != 'admin':
            prison_area = request.user.prison_id
            if not prison_area:
                return Response({
                    'code': 1,
                    'msg': '获取成功',
                    'data': [],
                    'num': 0,
                })

        success, message, result = RecordService.get_prison_messages(page, page_size, prison_area)

        return Response({
            'code': 1 if success else 0,
            'msg': message,
            'data': result.get('data', []),
            'num': result.get('num', 0),
        })