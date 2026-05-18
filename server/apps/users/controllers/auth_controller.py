from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.users.serializers import LoginSerializer
from apps.users.services import AuthService


class LoginController(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 0,
                'msg': '用户名和密码不能为空',
                'data': serializer.errors
            }, status=status.HTTP_200_OK)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        success, message, data = AuthService.login(username, password)

        if not success:
            return Response({
                'code': 0,
                'msg': message,
                'data': None
            }, status=status.HTTP_200_OK)

        return Response({
            'code': 1,
            'msg': message,
            'data': data
        })