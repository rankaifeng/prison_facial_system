class BaseService:
    """Base service class with common utilities"""

    @staticmethod
    def success_response(data=None, message='操作成功'):
        return {
            'code': 200,
            'message': message,
            'data': data
        }

    @staticmethod
    def error_response(code=400, message='操作失败', data=None):
        return {
            'code': code,
            'message': message,
            'data': data
        }