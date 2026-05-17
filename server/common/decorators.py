import functools
from rest_framework import status
from .responses import APIResponse


def require_auth(view_func):
    """要求登录装饰器"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return APIResponse.unauthorized(message='请先登录')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin(view_func):
    """要求管理员权限装饰器"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return APIResponse.unauthorized(message='请先登录')
        if getattr(request.user, 'role', None) != 'admin':
            return APIResponse.forbidden(message='需要管理员权限')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(role):
    """要求指定角色装饰器"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return APIResponse.unauthorized(message='请先登录')
            if getattr(request.user, 'role', None) != role:
                return APIResponse.forbidden(message=f'需要 {role} 权限')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator