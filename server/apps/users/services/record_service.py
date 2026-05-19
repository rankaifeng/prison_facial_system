import logging
import base64
import uuid
from django.db import transaction
from apps.users.repositories import RecordRepository, StatisticsRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class RecordService(BaseService):

    @staticmethod
    def save_image(base64_data, prefix='photo'):
        if not base64_data:
            return None

        # 如果是已存在的文件路径（包含 / 或 media/），直接返回
        if base64_data.startswith('/') or base64_data.startswith('media/'):
            return base64_data

        # 如果是URL，直接返回
        if base64_data.startswith('http'):
            return base64_data

        # 处理 base64 数据
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]

        try:
            image_data = base64.b64decode(base64_data)
            filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
            filepath = f"media/faces/{filename}"

            import os
            from django.conf import settings
            full_path = os.path.join(settings.MEDIA_ROOT, 'faces', filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(image_data)

            return f"/media/faces/{filename}"
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None

    @staticmethod
    def create_exit_record(
        prisoner_no, prisoner_name, prisoner_photo, prison_area, prison_area_name,
        exit_date, reason, police_face, swat_face, armed_police_signature,
        operator_id, operator_name
    ):
        with transaction.atomic():
            # 保存武警签名为图片文件
            signature_path = RecordService.save_image(armed_police_signature, 'signature')

            record = RecordRepository.create(
                prisoner_no=prisoner_no,
                prisoner_name=prisoner_name,
                prisoner_photo=prisoner_photo,
                prison_area=prison_area,
                prison_area_name=prison_area_name,
                type='exit',
                exit_date=exit_date,
                reason=reason,
                police_face=police_face,
                police_name=operator_name,
                swat_face=swat_face,
                armed_police_signature=signature_path,
                operator_id=operator_id,
                operator_name=operator_name,
                status='completed',
            )

            # 刑满释放不计入统计（因为不会回来）
            if reason == '刑满释放':
                logger.info(f"Exit record created (刑满释放，不统计): id={record.id}, prisoner={prisoner_no}")
                return True, '提交成功', {'id': record.id, 'status': record.status}

            stat = StatisticsRepository.get_or_create_daily_stats(prison_area, prison_area_name)
            stat.exit_count += 1
            stat.in_prison_count -= 1

            # 使用 JSONField 存储原因统计
            reason_stats = stat.reason_stats or {}
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            stat.reason_stats = reason_stats
            stat.save()

            logger.info(f"Exit record created: id={record.id}, prisoner={prisoner_no}, reason={reason}, total={stat.exit_count}")

            return True, '提交成功', {'id': record.id, 'status': record.status}

    @staticmethod
    def create_entry_record(
        prisoner_no, prisoner_name, prisoner_photo, prison_area, prison_area_name,
        entry_date, police_face, operator_id, operator_name
    ):
        with transaction.atomic():
            # 查找该罪犯的最后一条出监记录，获取出监原因
            exit_record = RecordRepository.get_last_exit_by_prisoner_no(prisoner_no)
            exit_reason = exit_record.reason if exit_record else None

            record = RecordRepository.create(
                prisoner_no=prisoner_no,
                prisoner_name=prisoner_name,
                prisoner_photo=prisoner_photo,
                prison_area=prison_area,
                prison_area_name=prison_area_name,
                type='entry',
                entry_date=entry_date,
                police_face=police_face,
                police_name=operator_name,
                operator_id=operator_id,
                operator_name=operator_name,
                status='completed',
            )

            stat = StatisticsRepository.get_or_create_daily_stats(prison_area, prison_area_name)
            stat.entry_count += 1
            stat.exit_count = max(0, stat.exit_count - 1)

            # 使用 JSONField 减少对应的出监原因计数
            if exit_reason:
                reason_stats = stat.reason_stats or {}
                current_count = reason_stats.get(exit_reason, 0)
                reason_stats[exit_reason] = max(0, current_count - 1)
                stat.reason_stats = reason_stats

            stat.save()
            logger.info(f"Entry record created: id={record.id}, prisoner={prisoner_no}, exit_reason={exit_reason}")

            return True, '提交成功', {'id': record.id, 'status': record.status}

    @staticmethod
    def list_records(type=None, start_date=None, end_date=None, prison_area=None,
                     prisoner_name=None, prisoner_no=None, reason=None, page=1, page_size=10):
        queryset = RecordRepository.filter(
            type=type, start_date=start_date, end_date=end_date, prison_area=prison_area,
            prisoner_name=prisoner_name, prisoner_no=prisoner_no, reason=reason
        )

        total = queryset.count()
        offset = (page - 1) * page_size
        records = queryset[offset:offset + page_size]

        data = []
        for record in records:
            # 构建完整的 HTTP 图片 URL
            # path 格式: /media/faces/xxx.jpg
            def build_image_url(path):
                if not path:
                    return None
                if path.startswith('http'):
                    return path
                return f"http://localhost:8000{path}"

            # 入监记录需要显示出监原因
            exit_reason = None
            if record.type == 'entry':
                exit_record = RecordRepository.get_last_exit_by_prisoner_no(record.prisoner_no)
                exit_reason = exit_record.reason if exit_record else None

            data.append({
                'id': record.id,
                'prisoner_no': record.prisoner_no,
                'prisoner_name': record.prisoner_name,
                'prisoner_photo': build_image_url(record.prisoner_photo),
                'prison_area_name': record.prison_area_name,
                'type': record.type,
                'reason': record.reason,  # 入监时填写的理由（可为空）
                'exit_reason': exit_reason,  # 出监原因（入监记录特有）
                'exit_date': record.exit_date,
                'entry_date': record.entry_date,
                'police_face': build_image_url(record.police_face),
                'police_name': record.police_name,
                'swat_face': build_image_url(record.swat_face),
                'swat_name': record.swat_name,
                'armed_police_signature': build_image_url(record.armed_police_signature),
                'armed_police_name': record.armed_police_name,
                'status': record.status,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return True, '获取成功', {
            'data': data,
            'num': total,
        }

    @staticmethod
    def get_prison_messages(page=1, page_size=20):
        """获取监狱消息列表"""
        exit_records = RecordRepository.get_active_exit_messages()

        messages = []
        for record in exit_records:
            has_entry = RecordRepository.has_entry_record(record.prisoner_no)
            if not has_entry:
                messages.append({
                    'id': record.id,
                    'prisoner_name': record.prisoner_name,
                    'prison_area_name': record.prison_area_name,
                    'exit_date': record.exit_date.strftime('%Y-%m-%d') if record.exit_date else None,
                    'reason': record.reason,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                })

        total = len(messages)
        offset = (page - 1) * page_size
        paginated = messages[offset:offset + page_size]

        return True, '获取成功', {'data': paginated, 'num': total}

    @staticmethod
    def get_record(record_id):
        record = RecordRepository.get_by_id(record_id)
        if not record:
            return False, '记录不存在', None

        def build_image_url(path):
            if not path:
                return None
            if path.startswith('http'):
                return path
            return f"http://localhost:8000{path}"

        return True, '获取成功', {
            'id': record.id,
            'prisoner_no': record.prisoner_no,
            'prisoner_name': record.prisoner_name,
            'prisoner_photo': build_image_url(record.prisoner_photo),
            'prison_area': record.prison_area,
            'prison_area_name': record.prison_area_name,
            'type': record.type,
            'reason': record.reason,
            'exit_date': record.exit_date,
            'entry_date': record.entry_date,
            'police_face': build_image_url(record.police_face),
            'police_name': record.police_name,
            'swat_face': build_image_url(record.swat_face),
            'swat_name': record.swat_name,
            'armed_police_signature': build_image_url(record.armed_police_signature),
            'armed_police_name': record.armed_police_name,
            'status': record.status,
        }