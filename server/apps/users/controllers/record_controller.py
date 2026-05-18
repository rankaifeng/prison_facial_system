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
        prisoner_photo = data.get('prisoner_photo')
        prison_area = data.get('prison_area')  # 前端传入的是 ID
        prison_area_name = get_prison_area_name(prison_area)  # 自动转换为名称
        exit_date = data.get('exit_date')
        reason_id = data.get('reason')  # 前端传入的是出监原因 ID
        reason = ExitTypeRepository.get_type_name(reason_id) if reason_id else None  # 转换为名称
        police_face = data.get('police_face')
        swat_face = data.get('swat_face')
        armed_police_signature = data.get('armed_police_signature')

        if not all([prisoner_no, prisoner_name, prison_area, exit_date, reason, police_face, swat_face, armed_police_signature]):
            return Response({
                'code': 0,
                'msg': '缺少必要参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        police_face_path = RecordService.save_image(police_face, 'police')
        swat_face_path = RecordService.save_image(swat_face, 'swat')
        signature_path = RecordService.save_image(armed_police_signature, 'signature')

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
        prisoner_photo = data.get('prisoner_photo')
        prison_area = data.get('prison_area')  # 前端传入的是 ID
        prison_area_name = get_prison_area_name(prison_area)  # 自动转换为名称
        entry_date = data.get('entry_date')
        police_face = data.get('police_face')

        if not all([prisoner_no, prisoner_name, prison_area, entry_date, police_face]):
            return Response({
                'code': 0,
                'msg': '缺少必要参数',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        police_face_path = RecordService.save_image(police_face, 'police')

        success, message, result = RecordService.create_entry_record(
            prisoner_no=prisoner_no,
            prisoner_name=prisoner_name,
            prisoner_photo=prisoner_photo,
            prison_area=prison_area,
            prison_area_name=prison_area_name,
            entry_date=entry_date,
            police_face=police_face_path,
            operator_id=request.user.id,
            operator_name=request.user.first_name or request.user.username,
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
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        prison_area = request.query_params.get('prison_area')
        prisoner_name = request.query_params.get('prisoner_name')
        prisoner_no = request.query_params.get('prisoner_no')
        reason = request.query_params.get('reason')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        if request.user.role != 'admin':
            prison_area = request.user.prison_id

        success, message, result = RecordService.list_records(
            type=record_type,
            start_date=start_date,
            end_date=end_date,
            prison_area=prison_area,
            prisoner_name=prisoner_name,
            prisoner_no=prisoner_no,
            reason=reason,
            page=page,
            page_size=page_size,
        )

        return Response({
            'code': 1,
            'msg': message,
            'data': result.get('data', []),
            'num': result.get('num', 0),
        })