from urllib.parse import urlparse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.models import PrisonerArchive


def _normalize_photo_url(url):
    """返回完整照片URL，兼容旧数据中的错误地址"""
    if not url:
        return url
    url = url.replace('http://10.2.48.86/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:80/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:8080/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.50.16:8080/', 'http://10.2.50.16/')
    return url


def _normalize_media_info(media_info):
    """处理媒体信息中的照片URL"""
    if not media_info:
        return media_info
    for item in media_info:
        if 'xp' in item:
            item['xp'] = _normalize_photo_url(item['xp'])
    return media_info


class ArchiveListController(APIView):
    """罪犯档案列表 - GET 分页查询，返回公安接口原始字段名"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prisoner_no = request.query_params.get('prisoner_no', '').strip()
        prisoner_name = request.query_params.get('prisoner_name', '').strip()
        prison_area = request.query_params.get('prison_area', '').strip()
        crime = request.query_params.get('crime', '').strip()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', request.query_params.get('limit', 10)))

        qs = PrisonerArchive.objects.all()

        if prisoner_no:
            qs = qs.filter(prisoner_no__icontains=prisoner_no)
        if prisoner_name:
            qs = qs.filter(prisoner_name__icontains=prisoner_name)
        if prison_area:
            qs = qs.filter(prison_area__icontains=prison_area)
        if crime:
            qs = qs.filter(crime__icontains=crime)

        total = qs.count()
        start = (page - 1) * page_size
        records = qs[start:start + page_size]

        data = []
        for r in records:
            item = r.basic_info.copy() if r.basic_info else {}
            item['mtxx'] = _normalize_media_info(r.media_info) or []
            item['synced_at'] = r.synced_at.strftime('%Y-%m-%d %H:%M:%S') if r.synced_at else ''
            data.append(item)

        return Response({
            'code': 1,
            'msg': 'success',
            'data': data,
            'num': total,
        })


class ArchiveDetailController(APIView):
    """罪犯档案详情 - GET 根据编号查询完整信息"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prisoner_no = request.query_params.get('prisoner_no', '').strip()
        if not prisoner_no:
            return Response({'code': 0, 'msg': '缺少罪犯编号', 'data': None})

        try:
            r = PrisonerArchive.objects.get(prisoner_no=prisoner_no)
        except PrisonerArchive.DoesNotExist:
            return Response({'code': 0, 'msg': '未找到该罪犯档案', 'data': None})

        item = r.basic_info.copy() if r.basic_info else {}
        item['mtxx'] = _normalize_media_info(r.media_info) or []
        item['synced_at'] = r.synced_at.strftime('%Y-%m-%d %H:%M:%S') if r.synced_at else ''

        return Response({
            'code': 1,
            'msg': 'success',
            'data': item,
        })
