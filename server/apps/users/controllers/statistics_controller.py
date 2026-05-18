from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.services import StatisticsService


class RealtimeStatisticsController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prison_area = None
        if request.user.role != 'admin':
            prison_area = request.user.prison_id

        success, message, data = StatisticsService.get_realtime_statistics(prison_area)

        return Response({
            'code': 1,
            'msg': message,
            'data': data
        })


class WorkStatisticsController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prison_area = None
        if request.user.role != 'admin':
            prison_area = request.user.prison_id

        success, message, data = StatisticsService.get_work_statistics(prison_area)

        return Response({
            'code': 1,
            'msg': message,
            'data': data
        })