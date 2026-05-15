import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
User = get_user_model()
from .serializers import UserSerializer, AccountCreateSerializer
from .jwt_utils import create_token, JWTAuthentication


def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            response.data = {
                'code': 401,
                'message': response.data.get('detail', '身份认证信息未提供。') if isinstance(response.data, dict) else '身份认证信息未提供。',
                'data': None
            }
        elif response.status_code == 403:
            response.data = {
                'code': 403,
                'message': response.data.get('detail', '无权限访问。') if isinstance(response.data, dict) else '无权限访问。',
                'data': None
            }

    return response


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


class AccountListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 403,
                'message': '无权限访问',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.all().order_by('-id')
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'name': user.first_name or user.username,
                'role': user.role,
                'role_name': user.role_name,
                'prison_id': user.prison_id,
                'prison_name': user.prison_name,
                'status': 'active',
            })

        return Response({
            'code': 200,
            'message': '获取成功',
            'data': data,
            'num': len(data)
        })

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 403,
                'message': '无权限访问',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AccountCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '参数错误',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        if User.objects.filter(username=username).exists():
            return Response({
                'code': 400,
                'message': '账号已存在',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        password = serializer.validated_data.get('password', '123456')
        name = serializer.validated_data.get('name', '')
        role = serializer.validated_data.get('role', 'operator')
        prison_id = serializer.validated_data.get('prison_id', '')
        prison_name = serializer.validated_data.get('prison_name', '')

        role_name_map = {
            'admin': '管理员',
            'operator': '操作员',
            'manager': '经理',
        }

        user = User.objects.create(
            username=username,
            password=make_password(password),
            first_name=name,
            role=role,
            role_name=role_name_map.get(role, '操作员'),
            prison_id=prison_id,
            prison_name=prison_name,
        )

        return Response({
            'code': 200,
            'message': '新增成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'name': user.first_name or user.username,
                'role': user.role,
                'role_name': user.role_name,
                'prison_id': user.prison_id,
                'prison_name': user.prison_name,
            }
        })


class AccountDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 403,
                'message': '无权限访问',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        account_id = request.data.get('id')
        if not account_id:
            return Response({
                'code': 400,
                'message': '缺少账号ID',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=account_id)
        except User.DoesNotExist:
            return Response({
                'code': 404,
                'message': '账号不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        if user.username == 'admin':
            return Response({
                'code': 400,
                'message': '不能删除管理员账号',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        user.delete()

        return Response({
            'code': 200,
            'message': '删除成功',
            'data': None
        })
