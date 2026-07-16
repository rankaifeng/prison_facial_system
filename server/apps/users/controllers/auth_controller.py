from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.serializers import LoginSerializer, ChangePasswordSerializer
from apps.users.services import AuthService
from apps.users.config.jwt import JWTAuthentication


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


class ChangePasswordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 0,
                'msg': '请填写旧密码和新密码',
                'data': serializer.errors
            }, status=status.HTTP_200_OK)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        success, message, data = AuthService.change_password(
            request.user, old_password, new_password
        )

        if not success:
            return Response({
                'code': 0,
                'msg': message,
                'data': None
            }, status=status.HTTP_200_OK)

        return Response({
            'code': 1,
            'msg': message,
            'data': None
        })