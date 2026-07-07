import base64
import logging
import os

import requests
import yaml
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.config import JWTAuthentication

logger = logging.getLogger(__name__)


def _load_dahua_smart_config():
    config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    smart = config.get('dahua_smart', {})
    return smart.get('base_url', '').rstrip('/'), smart.get('userName', ''), smart.get('password', '')


class SnapshotController(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        channel = request.query_params.get('channel', '1')

        base_url, username, password = _load_dahua_smart_config()
        if not base_url:
            return Response({'code': 0, 'msg': '智能事件设备未配置'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = f'{base_url}/cgi-bin/snapshot.cgi?channel={channel}'
        auth = requests.auth.HTTPDigestAuth(username, password) if username else None

        try:
            resp = requests.get(url, auth=auth, timeout=10)
            if resp.status_code != 200:
                return Response({'code': 0, 'msg': f'抓拍失败，状态码: {resp.status_code}'})

            image_b64 = base64.b64encode(resp.content).decode('ascii')
            return Response({'code': 1, 'data': {'image_base64': image_b64}})
        except requests.RequestException as e:
            logger.error(f'抓拍失败: {e}')
            return Response({'code': 0, 'msg': f'抓拍失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
