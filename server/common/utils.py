import uuid
import hashlib
from datetime import datetime


def get_client_ip(request):
    """获取客户端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def generate_unique_id(prefix=''):
    """生成唯一 ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_part = uuid.uuid4().hex[:8]
    return f"{prefix}{timestamp}{unique_part}" if prefix else f"{timestamp}{unique_part}"


def hash_string(text, algorithm='sha256'):
    """字符串哈希"""
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    else:
        return hashlib.sha256(text.encode()).hexdigest()


def paginate_queryset(queryset, page=1, page_size=10):
    """分页查询"""
    try:
        page = int(page)
        page_size = int(page_size)
    except (ValueError, TypeError):
        page, page_size = 1, 10

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10

    offset = (page - 1) * page_size
    total = queryset.count()
    items = queryset[offset:offset + page_size]

    return {
        'data': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
    }