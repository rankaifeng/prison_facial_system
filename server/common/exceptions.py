class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, message='业务处理失败', code=400, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class AuthenticationException(BusinessException):
    """认证异常"""

    def __init__(self, message='认证失败', code=401):
        super().__init__(message=message, code=code)


class PermissionException(BusinessException):
    """权限异常"""

    def __init__(self, message='无权限访问', code=403):
        super().__init__(message=message, code=code)


class ResourceNotFoundException(BusinessException):
    """资源不存在异常"""

    def __init__(self, message='资源不存在', code=404):
        super().__init__(message=message, code=code)


class ValidationException(BusinessException):
    """参数验证异常"""

    def __init__(self, message='参数验证失败', data=None):
        super().__init__(message=message, code=400, data=data)