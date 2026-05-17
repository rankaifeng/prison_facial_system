from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """统一 API 响应格式"""

    @staticmethod
    def success(data=None, message='操作成功', code=200, **kwargs):
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        response_data.update(kwargs)
        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def error(message='操作失败', code=400, data=None, http_status=None, **kwargs):
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        response_data.update(kwargs)
        http_status = http_status or (status.HTTP_400_BAD_REQUEST if code >= 400 else status.HTTP_200_OK)
        return Response(response_data, status=http_status)

    @staticmethod
    def unauthorized(message='未授权', data=None):
        return APIResponse.error(message=message, code=401, data=data, http_status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message='无权限访问', data=None):
        return APIResponse.error(message=message, code=403, data=data, http_status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def not_found(message='资源不存在', data=None):
        return APIResponse.error(message=message, code=404, data=data, http_status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def bad_request(message='请求参数错误', data=None):
        return APIResponse.error(message=message, code=400, data=data, http_status=status.HTTP_400_BAD_REQUEST)


def success_response(data=None, message='操作成功', **kwargs):
    """快捷响应 - 成功"""
    return APIResponse.success(data=data, message=message, **kwargs)


def error_response(message='操作失败', code=400, data=None, **kwargs):
    """快捷响应 - 失败"""
    return APIResponse.error(message=message, code=code, data=data, **kwargs)