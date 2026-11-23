import re
from datetime import date
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.dict import expand_prison_area_values, get_all_prison_areas, get_prison_area_name, get_prison_area_names
from apps.users.models import PrisonerArchive, ReleaseReview
from apps.users.services.photo_reminders import PHOTO_ACTIONS, archive_admission_date, assess_photo
from apps.users.services.release_check import (
    archive_release_dates, build_release_check, release_check_window, release_date_in_window,
)


def _parse_sentence_end(raw):
    """解析刑期止日，兼容 2026-08-05 / 2026.08.05 / 2026/08/05 / 2026年08月05日"""
    if not raw or not isinstance(raw, str):
        return None
    match = re.match(r'(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})', raw.strip())
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


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
    if not isinstance(media_info, list):
        return []
    return [
        {**item, 'xp': _normalize_photo_url(item['xp'])} if isinstance(item.get('xp'), str) else item
        for item in media_info if isinstance(item, dict)
    ]


class ArchiveListController(APIView):
    """罪犯档案列表 - GET 分页查询，返回公安接口原始字段名"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def get(self, request):
        prisoner_no = request.query_params.get('prisoner_no', '').strip()
        prisoner_name = request.query_params.get('prisoner_name', '').strip()
        prison_area = request.query_params.get('prison_area', '').strip()
        crime = request.query_params.get('crime', '').strip()
        release_start = request.query_params.get('release_start', '').strip()
        release_end = request.query_params.get('release_end', '').strip()
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

        # 按刑期止日（刑满释放日期）范围筛选；字段为多种格式的字符串，在 Python 层解析
        start_date = self._parse_date(release_start)
        end_date = self._parse_date(release_end)
        if start_date or end_date:
            matched_ids = []
            for r in qs:
                # 优先独立列；解析失败时回退 basic_info 原始 zr（兼容历史坏数据）
                d = _parse_sentence_end(r.sentence_end)
                if d is None and r.basic_info:
                    d = _parse_sentence_end(r.basic_info.get('zr'))
                if d is None:
                    continue
                if start_date and d < start_date:
                    continue
                if end_date and d > end_date:
                    continue
                matched_ids.append(r.pk)
            qs = qs.filter(pk__in=matched_ids)

        total = qs.count()
        start = (page - 1) * page_size
        records = qs[start:start + page_size]

        data = []
        today = timezone.localdate()
        for r in records:
            item = r.basic_info.copy() if r.basic_info else {}
            item['mtxx'] = _normalize_media_info(r.media_info) or []
            item['synced_at'] = r.synced_at.strftime('%Y-%m-%d %H:%M:%S') if r.synced_at else ''
            photo = assess_photo(r.media_info, archive_admission_date(r), today, _normalize_photo_url)
            item['photo_status'] = photo['status']
            item['photo_expired'] = photo['status'] == 'expired'
            # 已释放标记优先展示（凌晨同步会把 basic_info.zyxz 刷回"在押"）
            if r.is_released:
                item['zyxz'] = '已释放'
            data.append(item)

        return Response({
            'code': 1,
            'msg': 'success',
            'data': data,
            'num': total,
        })


class ArchivePhotoReminderController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        archives = PrisonerArchive.objects.filter(is_released=False)
        if request.user.role == 'admin' or request.user.is_superuser:
            visible_areas = [area['name'] for area in get_all_prison_areas()]
        else:
            assigned = request.user.prison_id or request.user.prison_name
            archives = archives.filter(prison_area__in=expand_prison_area_values(assigned))
            visible_areas = get_prison_area_names(assigned).split(',') if assigned else []
        today = timezone.localdate()
        rows = []
        for archive in archives.only(
            'prisoner_no', 'prisoner_name', 'prison_area', 'media_info', 'entry_date', 'basic_info',
        ).iterator():
            photo = assess_photo(archive.media_info, archive_admission_date(archive), today, _normalize_photo_url)
            if photo['status'] in PHOTO_ACTIONS:
                area = get_prison_area_name(archive.prison_area) or archive.prison_area or '未分配监区'
                visible_areas.append(area)
                rows.append({
                    'prisoner_no': archive.prisoner_no,
                    'prisoner_name': archive.prisoner_name,
                    'prison_area': area,
                    'status': photo['status'],
                    'entry_date': photo['entry_date'],
                    'action': PHOTO_ACTIONS[photo['status']],
                })
        response = Response({
            'code': 1, 'msg': 'success', 'data': rows,
            'areas': list(dict.fromkeys(area for area in visible_areas if area)),
        })
        response['Cache-Control'] = 'no-store'
        return response


class ReleaseReviewInput(serializers.Serializer):
    archive_id = serializers.IntegerField(min_value=1)
    release_date = serializers.DateField()
    decision = serializers.ChoiceField(choices=ReleaseReview.Decision.choices)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')


def _release_review_data(review):
    return {
        'decision': review.decision,
        'note': review.note,
        'reviewer': review.reviewer_username,
        'reviewed_at': timezone.localtime(review.reviewed_at).isoformat(),
    }


class ReleaseCheckController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_start, range_end = release_check_window(timezone.localdate())
        archives = PrisonerArchive.objects.only(
            'prisoner_no', 'prisoner_name', 'prison_area', 'sentence', 'sentence_start',
            'sentence_end', 'basic_info', 'media_info', 'is_released', 'entry_date',
        ).iterator()
        report = build_release_check(archives, range_start, _normalize_photo_url, range_end=range_end)
        reviews = {
            (review.archive_id, review.release_date.isoformat()): _release_review_data(review)
            for review in ReleaseReview.objects.filter(release_date__range=(range_start, range_end))
        }
        for row in report['rows']:
            row['review'] = reviews.get((row['id'], row['release_date']))
        response = Response({'code': 1, 'msg': 'success', 'data': report})
        response['Cache-Control'] = 'no-store'
        return response

    @transaction.atomic
    def post(self, request):
        serializer = ReleaseReviewInput(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 0, 'msg': '请检查核对结论和备注（最多500字）'})
        data = serializer.validated_data
        range_start, range_end = release_check_window(timezone.localdate())
        if not range_start <= data['release_date'] <= range_end:
            return Response({'code': 0, 'msg': '释放日期已超出未来7天范围，请关闭窗口后重新自检'})
        if data['decision'] == ReleaseReview.Decision.NEEDS_REVIEW and not data['note']:
            return Response({'code': 0, 'msg': '请在备注中填写待复核原因'})
        archive = PrisonerArchive.objects.select_for_update().filter(
            pk=data['archive_id'], is_released=False,
        ).first()
        scheduled = release_date_in_window(archive_release_dates(archive)[2:], range_start, range_end) if archive else None
        if scheduled != data['release_date']:
            return Response({'code': 0, 'msg': '此档案的预计释放日期已变化，请关闭窗口后重新自检'})
        review, _ = ReleaseReview.objects.update_or_create(
            archive=archive,
            release_date=scheduled,
            defaults={
                'decision': data['decision'],
                'note': data['note'],
                'reviewer_username': request.user.get_username(),
            },
        )
        return Response({'code': 1, 'msg': '核对结果已保存', 'data': _release_review_data(review)})


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
        # 显式返回常用字段（basic_info 中可能没有）
        item['sentence_end'] = r.sentence_end or item.get('zr', '')
        item['crime'] = r.crime or item.get('zm', '')
        item['prison_area'] = r.prison_area or item.get('db', '')
        # 已释放标记优先展示（凌晨同步会把 basic_info.zyxz 刷回"在押"）
        if r.is_released:
            item['zyxz'] = '已释放'

        return Response({
            'code': 1,
            'msg': 'success',
            'data': item,
        })
