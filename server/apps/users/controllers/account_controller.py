from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.serializers import AccountCreateSerializer
from apps.users.services import AccountService
from apps.users.dict import get_prison_area_name


class AccountListController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        username = request.query_params.get('username', '').strip()
        success, message, data = AccountService.list_accounts(username=username or None)

        return Response({
            'code': 1,
            'msg': message,
            'data': data,
            'num': len(data) if data else 0
        })

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        serializer = AccountCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 0,
                'msg': '参数错误',
                'data': serializer.errors
            }, status=status.HTTP_200_OK)

        data = serializer.validated_data
        prison_id = data.get('prison_id', '')
        success, message, result = AccountService.create_account(
            username=data.get('username'),
            password=data.get('password', '123456'),
            name=data.get('name', ''),
            role=data.get('role', 'user'),
            prison_id=prison_id,
            prison_name=get_prison_area_name(prison_id) if prison_id else '',
        )

        if not success:
            return Response({
                'code': 400,
                'msg': message,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 1,
            'msg': message,
            'data': result
        })


class AccountDeleteController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        account_id = request.data.get('id')
        if not account_id:
            return Response({
                'code': 400,
                'msg': '缺少账号ID',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        success, message, data = AccountService.delete_account(account_id)

        if not success:
            code = 404 if '不存在' in message else 400
            return Response({
                'code': code,
                'msg': message,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST if code == 400 else status.HTTP_404_NOT_FOUND)

        return Response({
            'code': 1,
            'msg': message,
            'data': None
        })


class AccountUpdateController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        account_id = request.data.get('id')
        if not account_id:
            return Response({
                'code': 400,
                'msg': '缺少账号ID',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        prison_id = request.data.get('prison_id', '')
        role = request.data.get('role', 'user')
        update_data = {
            'first_name': request.data.get('name', ''),
            'role': role,
            'role_name': '管理员' if role == 'admin' else '普通用户',
            'prison_id': prison_id,
            'prison_name': get_prison_area_name(prison_id) if prison_id else '',
        }
        password = request.data.get('password')
        if password:
            update_data['password'] = password

        success, message, data = AccountService.update_account(account_id, **update_data)
        if not success:
            return Response({
                'code': 404,
                'msg': message,
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'code': 1,
            'msg': message,
            'data': data
        })


class AccountGetPasswordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        admin_password = request.data.get('admin_password')
        account_id = request.data.get('id')

        if not admin_password or not account_id:
            return Response({
                'code': 0,
                'msg': '参数不完整',
                'data': None
            }, status=status.HTTP_200_OK)

        success, msg, data = AccountService.get_password(
            request.user, admin_password, account_id
        )

        if not success:
            return Response({
                'code': 0,
                'msg': msg,
                'data': None
            }, status=status.HTTP_200_OK)

        return Response({
            'code': 1,
            'msg': msg,
            'data': data
        })


class AccountResetPasswordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)

        account_id = request.data.get('id')
        if not account_id:
            return Response({
                'code': 400,
                'msg': '缺少账号ID',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('password') or request.data.get('new_password') or '123456'
        success, message, data = AccountService.update_account(account_id, password=new_password)
        if not success:
            return Response({
                'code': 404,
                'msg': message,
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'code': 1,
            'msg': '重置成功',
            'data': data
        })
