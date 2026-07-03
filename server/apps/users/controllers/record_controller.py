from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
from apps.users.services import RecordService
from apps.users.dict import get_prison_area_name
from apps.users.repositories import ExitTypeRepository


class ExitRecordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        prisoner_no = data.get('prisoner_no')
        prisoner_name = data.get('prisoner_name')
        prisoner_photo = data.get('prisoner_photo') or ''
        prison_area = data.get('prison_area')  # 前端传入的是 ID
        prison_area_name = get_prison_area_name(prison_area)  # 自动转换为名称
        exit_date = data.get('exit_date')
        reason_id = data.get('reason')  # 前端传入的是出监原因 ID
        reason = ExitTypeRepository.get_type_name(reason_id) if reason_id else None  # 转换为名称
        police_face = data.get('police_face')
        swat_face = data.get('swat_face')
        armed_police_signature = data.get('armed_police_signature')
        hospital_name = data.get('hospital_name')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        attachments = request.FILES.getlist('attachments') if request.FILES else []

        if not all([prisoner_no, prisoner_name, prison_area, exit_date, reason, police_face, swat_face, armed_police_signature]):
            return Response({
                'code': 0,
                'msg': '缺少必要参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 外出就医必须有医院信息
        if reason == '外出就医' and not hospital_name:
            return Response({
                'code': 0,
                'msg': '外出就医必须填写医院名称',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        police_face_path = RecordService.save_image(police_face, 'police')
        swat_face_path = RecordService.save_image(swat_face, 'swat')
        signature_path = RecordService.save_image(armed_police_signature, 'signature')

        # 处理附件
        attachment_paths = []
        for file in attachments:
            file_path = RecordService.save_file(file)
            if file_path:
                attachment_paths.append(file_path)

        success, message, result = RecordService.create_exit_record(
            prisoner_no=prisoner_no,
            prisoner_name=prisoner_name,
            prisoner_photo=prisoner_photo,
            prison_area=prison_area,
            prison_area_name=prison_area_name,
            exit_date=exit_date,
            reason=reason,
            police_face=police_face_path,
            swat_face=swat_face_path,
            armed_police_signature=signature_path,
            operator_id=request.user.id,
            operator_name=request.user.first_name or request.user.username,
            hospital_name=hospital_name,
            attachments=attachment_paths,
            start_time=start_time,
            end_time=end_time,
        )

        if not success:
            return Response({
                'code': 0,
                'msg': message,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 1,
            'msg': message,
            'data': result
        })


class EntryRecordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        prisoner_no = data.get('prisoner_no')
        prisoner_name = data.get('prisoner_name')
        prisoner_photo = data.get('prisoner_photo') or ''
        prison_area = data.get('prison_area')  # 前端传入的是 ID
        prison_area_name = get_prison_area_name(prison_area)  # 自动转换为名称
        entry_date = data.get('entry_date')
        police_face = data.get('police_face')
        entry_status = data.get('entry_status', 'normal')
        abnormal_reason = data.get('abnormal_reason', '')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([prisoner_no, prisoner_name, prison_area, entry_date, police_face]):
            return Response({
                'code': 0,
                'msg': '缺少必要参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        entry_datetime = RecordService.parse_datetime(entry_date)
        if not entry_datetime:
            return Response({
                'code': 0,
                'msg': '日期格式错误，请使用 YYYY-MM-DD 或 YYYY-MM-DD HH:mm 格式',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        police_face_path = RecordService.save_image(police_face, 'police')

        success, message, result = RecordService.create_entry_record(
            prisoner_no=prisoner_no,
            prisoner_name=prisoner_name,
            prisoner_photo=prisoner_photo,
            prison_area=prison_area,
            prison_area_name=prison_area_name,
            entry_date=entry_datetime,
            police_face=police_face_path,
            operator_id=request.user.id,
            operator_name=request.user.first_name or request.user.username,
            entry_status=entry_status,
            abnormal_reason=abnormal_reason,
            start_time=start_time,
            end_time=end_time,
        )

        if not success:
            return Response({
                'code': 0,
                'msg': message,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 1,
            'msg': message,
            'data': result
        })


class ReturnRecordController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        prisoner_no = data.get('prisoner_no')
        prisoner_name = data.get('prisoner_name')
        prisoner_photo = data.get('prisoner_photo') or ''
        prison_area = data.get('prison_area')  # 前端传入的是 ID
        prison_area_name = get_prison_area_name(prison_area)  # 自动转换为名称
        entry_date = data.get('entry_date')
        police_face = data.get('police_face')
        entry_status = data.get('entry_status', 'normal')
        abnormal_reason = data.get('abnormal_reason', '')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([prisoner_no, prisoner_name, prison_area, entry_date, police_face]):
            return Response({
                'code': 0,
                'msg': '缺少必要参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 解析日期时间，支持 'YYYY-MM-DD' 和 'YYYY-MM-DD HH:mm' 格式
        entry_datetime = RecordService.parse_datetime(entry_date)
        if not entry_datetime:
            return Response({
                'code': 0,
                'msg': '日期格式错误，请使用 YYYY-MM-DD 或 YYYY-MM-DD HH:mm 格式',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        police_face_path = RecordService.save_image(police_face, 'police')

        success, message, result = RecordService.create_return_record(
            prisoner_no=prisoner_no,
            prisoner_name=prisoner_name,
            prisoner_photo=prisoner_photo,
            prison_area=prison_area,
            prison_area_name=prison_area_name,
            entry_date=entry_datetime,
            police_face=police_face_path,
            operator_id=request.user.id,
            operator_name=request.user.first_name or request.user.username,
            entry_status=entry_status,
            abnormal_reason=abnormal_reason,
            start_time=start_time,
            end_time=end_time,
        )

        if not success:
            return Response({
                'code': 0,
                'msg': message,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'code': 1,
            'msg': message,
            'data': result
        })


class RecordListController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        record_type = request.query_params.get('type')
        start_timestamp = request.query_params.get('start_timestamp')
        end_timestamp = request.query_params.get('end_timestamp')
        prison_area = request.query_params.get('prison_area')
        prisoner_name = request.query_params.get('prisoner_name')
        prisoner_no = request.query_params.get('prisoner_no')
        reason = request.query_params.get('reason')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', request.query_params.get('page_size', 10)))

        if request.user.role != 'admin':
            prison_area = request.user.prison_id

        success, message, result = RecordService.list_records(
            type=record_type,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            prison_area=prison_area,
            prisoner_name=prisoner_name,
            prisoner_no=prisoner_no,
            reason=reason,
            page=page,
            page_size=page_size,
            request_host=request.get_host(),
        )

        return Response({
            'code': 1,
            'msg': message,
            'data': result.get('data', []),
            'num': result.get('num', 0),
        })


class RecordExportController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        record_type = request.query_params.get('type')
        start_timestamp = request.query_params.get('start_timestamp')
        end_timestamp = request.query_params.get('end_timestamp')
        prison_area = request.query_params.get('prison_area')
        prisoner_name = request.query_params.get('prisoner_name')
        prisoner_no = request.query_params.get('prisoner_no')
        reason = request.query_params.get('reason')

        if request.user.role != 'admin':
            prison_area = request.user.prison_id

        success, message, result = RecordService.export_records(
            type=record_type,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            prison_area=prison_area,
            prisoner_name=prisoner_name,
            prisoner_no=prisoner_no,
            reason=reason,
            request_host=request.get_host(),
        )

        return Response({
            'code': 1,
            'msg': message,
            'data': result,
        })
