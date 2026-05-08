import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .jwt_utils import create_token

logger = logging.getLogger(__name__)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username') or request.query_params.get('username')
        password = request.data.get('password') or request.query_params.get('password')
        logger.info(f"username: {username}, password: {password}")

        if not username or not password:
            return Response({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        logger.info(f"authenticate result: {user}")

        if not user:
            return Response({
                'code': 401,
                'message': '用户名或密码错误',
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = create_token(user)
        logger.info(f"Generated token: {token}")

        user_data = UserSerializer(user).data
        response_data = {'token': token}
        response_data.update(user_data)

        return Response({
            'code': 200,
            'message': '登录成功',
            'data': response_data
        })
