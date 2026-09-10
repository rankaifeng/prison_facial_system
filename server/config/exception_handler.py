from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, AuthenticationFailed):
            return Response({
                'code': 401,
                'msg': str(exc.detail) if hasattr(exc, 'detail') else '登录已过期，请重新登录',
                'data': None
            }, status=status.HTTP_200_OK)
        elif response.status_code == 401:
            return Response({
                'code': 401,
                'msg': '登录已过期，请重新登录',
                'data': None
            }, status=status.HTTP_200_OK)
        elif response.status_code == 403:
            return Response({
                'code': 0,
                'msg': '无权限访问',
                'data': None
            }, status=status.HTTP_200_OK)
        elif response.status_code == 404:
            return Response({
                'code': 0,
                'msg': '资源不存在',
                'data': None
            }, status=status.HTTP_200_OK)
        elif response.status_code >= 500:
            return Response({
                'code': 0,
                'msg': '服务器内部错误',
                'data': None
            }, status=status.HTTP_200_OK)

        detail = response.data.get('detail', '') if isinstance(response.data, dict) else str(response.data)
        return Response({
            'code': 0,
            'msg': detail,
            'data': None
        }, status=status.HTTP_200_OK)

    return response