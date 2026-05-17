from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.serializers import ExitTypeSerializer
from apps.users.services import ExitTypeService


class ExitTypeListController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        type_name = request.query_params.get('type_name', '')
        success, message, data = ExitTypeService.list_exit_types(type_name)

        return Response({
            'code': 200,
            'message': message,
            'data': data,
            'num': len(data) if data else 0,
        })


class ExitTypeAddController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExitTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '参数错误',
                'data': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        success, message, result = ExitTypeService.create_exit_type(
            type_name=data.get('type_name'),
            parent_id=data.get('parent_id'),
            sort_order=data.get('sort_order', 0),
            status=data.get('status', 'active'),
        )
        if not success:
            return Response({
                'code': 400,
                'message': message,
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 200,
            'message': message,
            'data': result,
        })


class ExitTypeUpdateController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exit_type_id = request.data.get('id')
        if not exit_type_id:
            return Response({
                'code': 400,
                'message': '缺少出监原因ID',
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ExitTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '参数错误',
                'data': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        success, message, result = ExitTypeService.update_exit_type(
            exit_type_id=exit_type_id,
            type_name=data.get('type_name'),
            parent_id=data.get('parent_id'),
            sort_order=data.get('sort_order', 0),
            status=data.get('status', 'active'),
        )
        if not success:
            return Response({
                'code': 400,
                'message': message,
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 200,
            'message': message,
            'data': result,
        })


class ExitTypeDeleteController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exit_type_id = request.data.get('id')
        if not exit_type_id:
            return Response({
                'code': 400,
                'message': '缺少出监原因ID',
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        success, message, data = ExitTypeService.delete_exit_type(exit_type_id)
        if not success:
            return Response({
                'code': 400,
                'message': message,
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 200,
            'message': message,
            'data': data,
        })
