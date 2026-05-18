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
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 20))

        success, message, result = RecordService.get_prison_messages(page, page_size)

        return Response({
            'code': 1 if success else 0,
            'msg': message,
            'data': result.get('data', []),
            'num': result.get('num', 0),
        })