import logging
import base64
import uuid
import threading
from django.db import transaction
from apps.users.repositories import RecordRepository, StatisticsRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


def _run_video_generation_async(record_id):
    """在新线程中异步执行视频生成，不阻塞主线程"""
    from apps.users.tasks import generate_exit_video
    try:
        generate_exit_video(record_id)
    except Exception as e:
        logger.error(f"视频生成线程异常: record_id={record_id}, error={e}")


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
    def parse_datetime(value):
        """解析日期时间字符串，支持 'YYYY-MM-DD' 和 'YYYY-MM-DD HH:mm' 格式"""
        if not value:
            return None
        from datetime import datetime
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M')
            return dt.date()  # 返回日期部分，忽略时间
        except ValueError:
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return None

    @staticmethod
    def save_file(file):
        """保存上传的文件"""
        if not file:
            return None
        try:
            import os
            import uuid
            from django.conf import settings
            ext = os.path.splitext(file.name)[1]
            filename = f"attachment_{uuid.uuid4().hex}{ext}"
            filepath = f"media/attachments/{filename}"
            full_path = os.path.join(settings.MEDIA_ROOT, 'attachments', filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            return f"/media/attachments/{filename}"
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return None

    @staticmethod
    def create_exit_record(
        prisoner_no, prisoner_name, prisoner_photo, prison_area, prison_area_name,
        exit_date, reason, police_face, swat_face, armed_police_signature,
        operator_id, operator_name, hospital_name=None, attachments=None,
        start_time=None, end_time=None
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
                hospital_name=hospital_name,
                status='completed',
                attachments=attachments or [],
                start_time=start_time,
                end_time=end_time,
                video_url='',
            )

            # 更新统计（所有出监原因都计入，统一用 prison_area_name 作为 key）
            stat = StatisticsRepository.get_or_create_daily_stats(prison_area_name, prison_area_name)
            stat.exit_count += 1

            reason_stats = stat.reason_stats or {}
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            stat.reason_stats = reason_stats

            # 只有刑满释放才扣减在监人数，标记档案为已释放
            if reason == '刑满释放':
                stat.in_prison_count -= 1
                from apps.users.models import PrisonerArchive
                PrisonerArchive.objects.filter(prisoner_no=prisoner_no).update(is_released=True)
                logger.info(f"刑满释放: 标记已释放 prisoner_no={prisoner_no}")

            stat.save()

            logger.info(f"Exit record created: id={record.id}, prisoner={prisoner_no}, reason={reason}, total={stat.exit_count}")

            # 启动后台线程生成视频
            t = threading.Thread(target=_run_video_generation_async, args=(record.id,))
            t.start()

            return True, '提交成功', {'id': record.id, 'status': record.status}

    @staticmethod
    def create_entry_record(
        prisoner_no, prisoner_name, prisoner_photo, prison_area, prison_area_name,
        entry_date, police_face, operator_id, operator_name, entry_status=None, abnormal_reason=None,
        start_time=None, end_time=None
    ):
        from datetime import date as date_cls

        with transaction.atomic():
            # 查找该罪犯的最后一条出监记录
            exit_record = RecordRepository.get_last_exit_by_prisoner_no(prisoner_no)
            exit_reason = exit_record.reason if exit_record else None
            print(f'[入监DEBUG] prisoner_no={prisoner_no}, prison_area={prison_area}, exit_record={exit_record}, exit_reason={exit_reason}')

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
                status=entry_status or 'normal',
                abnormal_reason=abnormal_reason or '',
                start_time=start_time,
                end_time=end_time,
                video_url='',
            )

            # 统一用 prison_area_name 作为统计 key，避免 ID/名称不一致
            stat = StatisticsRepository.get_or_create_daily_stats(prison_area_name, prison_area_name)
            stat.entry_count += 1
            print(f'[入监DEBUG] 今日stat: id={stat.id}, prison_area={stat.prison_area}, exit_count={stat.exit_count}')

            # 如果有对应的出监记录，回退出监统计
            if exit_record:
                today = date_cls.today()
                exit_date = exit_record.exit_date
                print(f'[入监DEBUG] exit_date={exit_date}, today={today}')

                if exit_date and exit_date != today:
                    exit_day_stat = StatisticsRepository.get_or_create_daily_stats(
                        prison_area_name, prison_area_name, target_date=exit_date
                    )
                    print(f'[入监DEBUG] 跨天: exit_count {exit_day_stat.exit_count}->{max(0, exit_day_stat.exit_count - 1)}')
                    exit_day_stat.exit_count = max(0, exit_day_stat.exit_count - 1)
                    if exit_reason:
                        rs = exit_day_stat.reason_stats or {}
                        rs[exit_reason] = max(0, rs.get(exit_reason, 0) - 1)
                        exit_day_stat.reason_stats = rs
                    # 只有刑满释放才恢复在监人数
                    if exit_reason == '刑满释放':
                        exit_day_stat.in_prison_count += 1
                    exit_day_stat.save()
                else:
                    print(f'[入监DEBUG] 同天: exit_count {stat.exit_count}->{max(0, stat.exit_count - 1)}')
                    stat.exit_count = max(0, stat.exit_count - 1)
                    if exit_reason:
                        reason_stats = stat.reason_stats or {}
                        reason_stats[exit_reason] = max(0, reason_stats.get(exit_reason, 0) - 1)
                        stat.reason_stats = reason_stats
                    # 只有刑满释放才恢复在监人数
                    if exit_reason == '刑满释放':
                        stat.in_prison_count += 1

                # 刑满释放后回监，恢复档案为在押状态
                if exit_reason == '刑满释放':
                    from apps.users.models import PrisonerArchive
                    PrisonerArchive.objects.filter(prisoner_no=prisoner_no).update(is_released=False)
                    logger.info(f"入监恢复档案: prisoner_no={prisoner_no}")
            else:
                print(f'[入监DEBUG] 警告: 未找到罪犯 {prisoner_no} 的出监记录')

            stat.save()
            print(f'[入监DEBUG] 保存后: exit_count={stat.exit_count}, entry_count={stat.entry_count}')
            logger.info(f"Entry record created: id={record.id}, prisoner={prisoner_no}")

            # 启动后台线程生成视频
            t = threading.Thread(target=_run_video_generation_async, args=(record.id,))
            t.start()

            return True, '提交成功', {'id': record.id, 'status': record.status}

    @staticmethod
    def create_return_record(
        prisoner_no, prisoner_name, prisoner_photo, prison_area, prison_area_name,
        entry_date, police_face, operator_id, operator_name, entry_status=None, abnormal_reason=None,
        start_time=None, end_time=None
    ):
        """回监记录：与入监类似，但需要处理同一编号回监时的统计回退逻辑"""
        from datetime import date as date_cls

        with transaction.atomic():
            # 查找该罪犯的最后一条出监记录，获取出监原因
            exit_record = RecordRepository.get_last_exit_by_prisoner_no(prisoner_no)
            exit_reason = exit_record.reason if exit_record else None

            print(f'[回监DEBUG] prisoner_no={prisoner_no}, prison_area={prison_area}, exit_record={exit_record}, exit_reason={exit_reason}')

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
                status=entry_status or 'normal',
                abnormal_reason=abnormal_reason or '',
                start_time=start_time,
                end_time=end_time,
            )

            # 今日入监数 +1，统一用 prison_area_name 作为统计 key
            stat = StatisticsRepository.get_or_create_daily_stats(prison_area_name, prison_area_name)
            stat.entry_count += 1
            print(f'[回监DEBUG] 今日stat: id={stat.id}, prison_area={stat.prison_area}, exit_count={stat.exit_count}, entry_count={stat.entry_count}')

            # 如果有对应的出监记录，需要回退出监统计数据
            if exit_record:
                today = date_cls.today()
                exit_date = exit_record.exit_date
                print(f'[回监DEBUG] exit_date={exit_date}, today={today}, same_day={exit_date == today}')

                if exit_date and exit_date != today:
                    # 出监发生在其他天：修改出监那天的统计
                    exit_day_stat = StatisticsRepository.get_or_create_daily_stats(
                        prison_area_name, prison_area_name, target_date=exit_date
                    )
                    print(f'[回监DEBUG] 跨天修改: stat_id={exit_day_stat.id}, exit_count={exit_day_stat.exit_count}->{max(0, exit_day_stat.exit_count - 1)}')
                    exit_day_stat.exit_count = max(0, exit_day_stat.exit_count - 1)
                    if exit_reason:
                        rs = exit_day_stat.reason_stats or {}
                        rs[exit_reason] = max(0, rs.get(exit_reason, 0) - 1)
                        exit_day_stat.reason_stats = rs
                    # 只有刑满释放才恢复在监人数
                    if exit_reason == '刑满释放':
                        exit_day_stat.in_prison_count += 1
                    exit_day_stat.save()
                    # 只有刑满释放才恢复今日在监人数
                    if exit_reason == '刑满释放':
                        stat.in_prison_count += 1
                else:
                    # 出监发生在今天：修改今日统计（与之前逻辑一致）
                    print(f'[回监DEBUG] 同天修改: exit_count={stat.exit_count}->{max(0, stat.exit_count - 1)}')
                    stat.exit_count = max(0, stat.exit_count - 1)
                    if exit_reason:
                        reason_stats = stat.reason_stats or {}
                        current_count = reason_stats.get(exit_reason, 0)
                        reason_stats[exit_reason] = max(0, current_count - 1)
                        stat.reason_stats = reason_stats
                    # 只有刑满释放才恢复在监人数
                    if exit_reason == '刑满释放':
                        stat.in_prison_count += 1

                # 刑满释放后回监，恢复档案为在押状态
                if exit_reason == '刑满释放':
                    from apps.users.models import PrisonerArchive
                    PrisonerArchive.objects.filter(prisoner_no=prisoner_no).update(is_released=False)
                    logger.info(f"回监恢复档案: prisoner_no={prisoner_no}")
            else:
                # 没有对应出监记录，说明该编号之前不在统计数据中（可能是新收入监）
                print(f'[回监DEBUG] 警告: 未找到罪犯 {prisoner_no} 的出监记录')
                stat.in_prison_count += 1

            stat.save()
            print(f'[回监DEBUG] 保存后: exit_count={stat.exit_count}, entry_count={stat.entry_count}')
            logger.info(f"Return record created: id={record.id}, prisoner={prisoner_no}, exit_reason={exit_reason}")

            # 启动后台线程生成视频
            t = threading.Thread(target=_run_video_generation_async, args=(record.id,))
            t.start()

            return True, '提交成功', {'id': record.id, 'status': record.status}

    @staticmethod
    def list_records(type=None, start_timestamp=None, end_timestamp=None, prison_area=None,
                     prisoner_name=None, prisoner_no=None, reason=None, page=1, page_size=10,
                     request_host=None):
        queryset = RecordRepository.filter(
            type=type, start_timestamp=start_timestamp, end_timestamp=end_timestamp, prison_area=prison_area,
            prisoner_name=prisoner_name, prisoner_no=prisoner_no, reason=reason
        )

        total = queryset.count()
        offset = (page - 1) * page_size
        records = queryset[offset:offset + page_size]

        host = request_host or 'localhost:8000'

        data = []
        for record in records:
            def build_url(path):
                if not path:
                    return None
                if path.startswith('http'):
                    return path
                return f"http://{host}{path}"

            # 入监记录需要显示出监原因
            exit_reason = None
            if record.type == 'entry':
                exit_record = RecordRepository.get_last_exit_by_prisoner_no(record.prisoner_no)
                exit_reason = exit_record.reason if exit_record else None

            data.append({
                'id': record.id,
                'prisoner_no': record.prisoner_no,
                'prisoner_name': record.prisoner_name,
                'prisoner_photo': build_url(record.prisoner_photo),
                'prison_area_name': record.prison_area_name,
                'type': record.type,
                'reason': record.reason,  # 入监时填写的理由（可为空）
                'exit_reason': exit_reason,  # 出监原因（入监记录特有）
                'exit_date': record.exit_date.strftime('%Y-%m-%d') if record.exit_date else None,
                'entry_date': record.entry_date.strftime('%Y-%m-%d') if record.entry_date else None,
                'police_face': build_url(record.police_face),
                'police_name': record.police_name,
                'swat_face': build_url(record.swat_face),
                'swat_name': record.swat_name,
                'armed_police_signature': build_url(record.armed_police_signature),
                'armed_police_name': record.armed_police_name,
                'hospital_name': record.hospital_name,
                'start_time': record.start_time,
                'end_time': record.end_time,
                'video_url': build_url(record.video_url),
                'attachments': [build_url(a) for a in (record.attachments or [])],
                'status': record.status,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return True, '获取成功', {
            'data': data,
            'num': total,
        }

    @staticmethod
    def get_prison_messages(page=1, page_size=20, prison_area=None):
        """获取监狱消息列表 - 当天刑满释放人员"""
        from datetime import date
        from apps.users.models import PrisonerArchive

        today = date.today().strftime('%Y.%m.%d')
        qs = PrisonerArchive.objects.filter(sentence_end=today, is_released=False)
        if prison_area:
            qs = qs.filter(prison_area=prison_area)

        total = qs.count()
        offset = (page - 1) * page_size
        records = qs[offset:offset + page_size]

        data = [{
            'id': r.id,
            'prisoner_name': r.prisoner_name,
            'prison_area_name': r.prison_area,
            'exit_date': r.sentence_end,
            'reason': '刑满释放',
            'hospital_type': '',
            'hospital_name': '',
        } for r in records]

        return True, '获取成功', {'data': data, 'num': total}

    @staticmethod
    def get_record(record_id, request_host=None):
        record = RecordRepository.get_by_id(record_id)
        if not record:
            return False, '记录不存在', None

        host = request_host or 'localhost:8000'

        def build_url(path):
            if not path:
                return None
            if path.startswith('http'):
                return path
            return f"http://{host}{path}"

        return True, '获取成功', {
            'id': record.id,
            'prisoner_no': record.prisoner_no,
            'prisoner_name': record.prisoner_name,
            'prisoner_photo': build_url(record.prisoner_photo),
            'prison_area': record.prison_area,
            'prison_area_name': record.prison_area_name,
            'type': record.type,
            'reason': record.reason,
            'exit_date': record.exit_date.strftime('%Y-%m-%d') if record.exit_date else None,
            'entry_date': record.entry_date.strftime('%Y-%m-%d') if record.entry_date else None,
            'police_face': build_url(record.police_face),
            'police_name': record.police_name,
            'swat_face': build_url(record.swat_face),
            'swat_name': record.swat_name,
            'armed_police_signature': build_url(record.armed_police_signature),
            'armed_police_name': record.armed_police_name,
            'hospital_type': record.hospital_type,
            'hospital_name': record.hospital_name,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'video_url': build_url(record.video_url),
            'status': record.status,
        }

    @staticmethod
    def export_records(type=None, start_timestamp=None, end_timestamp=None, prison_area=None,
                       prisoner_name=None, prisoner_no=None, reason=None, request_host=None):
        """导出记录为CSV数据"""
        queryset = RecordRepository.filter(
            type=type, start_timestamp=start_timestamp, end_timestamp=end_timestamp, prison_area=prison_area,
            prisoner_name=prisoner_name, prisoner_no=prisoner_no, reason=reason
        )

        records = queryset[:5000]  # 限制最多导出5000条

        host = request_host or 'localhost:8000'

        def build_url(path):
            if not path:
                return ''
            if path.startswith('http'):
                return path
            return f"http://{host}{path}"

        data = []
        for record in records:
            # 入监记录需要显示出监原因
            exit_reason = None
            if record.type == 'entry':
                exit_record = RecordRepository.get_last_exit_by_prisoner_no(record.prisoner_no)
                exit_reason = exit_record.reason if exit_record else None

            data.append({
                'prison_area_name': record.prison_area_name,
                'prisoner_name': record.prisoner_name,
                'prisoner_no': record.prisoner_no,
                'type': '出监' if record.type == 'exit' else '入监',
                'exit_date': record.exit_date.strftime('%Y-%m-%d') if record.exit_date else '',
                'entry_date': record.entry_date.strftime('%Y-%m-%d') if record.entry_date else '',
                'reason': record.reason or '',
                'exit_reason': exit_reason or '',
                'police_face': build_url(record.police_face),
                'police_name': record.police_name or '',
                'swat_face': build_url(record.swat_face),
                'swat_name': record.swat_name or '',
                'armed_police_signature': build_url(record.armed_police_signature),
                'armed_police_name': record.armed_police_name or '',
                'hospital_name': record.hospital_name if record.reason == '外出就医' else '',
                'video': 'https://www.w3schools.com/html/mov_bbb.mp4',
                'status': record.status,
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return True, '导出成功', data