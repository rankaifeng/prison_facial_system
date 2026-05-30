from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.config import JWTAuthentication
import yaml
import os


def load_cameras_config():
    """加载摄像头配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config', 'cameras.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return {'cameras': []}


class VideoStreamUrlController(APIView):
    """生成录像播放地址"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        camera_index = int(request.query_params.get('camera', 0))  # 0 或 1

        if not start_time or not end_time:
            return Response({
                'code': 0,
                'msg': '缺少开始时间或结束时间',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        config = load_cameras_config()
        cameras = config.get('cameras', [])

        if camera_index >= len(cameras):
            return Response({
                'code': 0,
                'msg': '摄像头不存在',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        camera = cameras[camera_index]
        if not camera.get('enabled'):
            return Response({
                'code': 0,
                'msg': '摄像头未启用',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        rtsp_url = camera.get('rtsp_url', '')
        if not rtsp_url:
            return Response({
                'code': 0,
                'msg': '摄像头RTSP地址未配置',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 构建完整的RTSP地址，带时间范围
        full_url = f"{rtsp_url}/?starttime={start_time}&endtime={end_time}"

        return Response({
            'code': 1,
            'msg': 'success',
            'data': {
                'url': full_url,
                'camera_name': camera.get('name'),
                'channel': camera.get('channel'),
            }
        })


class CameraListController(APIView):
    """获取摄像头列表"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = load_cameras_config()
        cameras = config.get('cameras', [])

        camera_list = [
            {
                'index': idx,
                'name': cam.get('name'),
                'channel': cam.get('channel'),
                'enabled': cam.get('enabled', False),
            }
            for idx, cam in enumerate(cameras)
        ]

        return Response({
            'code': 1,
            'msg': 'success',
            'data': camera_list
        })