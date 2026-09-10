import os
import threading
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'false':
            from apps.users.services.dahua_event_service import DahuaEventService
            DahuaEventService.start()
            # 启动后自动注册手持终端回调地址
            threading.Thread(target=self._register_handheld_callback, daemon=True).start()

    def _register_handheld_callback(self):
        import time
        import logging
        import requests
        import yaml
        from django.conf import settings

        logger = logging.getLogger(__name__)
        time.sleep(5)  # 等待服务完全启动

        config_path = os.path.join(settings.BASE_DIR, 'config', 'handheld_device.yml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            return

        device = cfg.get('device', {})
        ip = device.get('ip', '')
        port = device.get('port', 8090)
        password = device.get('password', '')
        callback_url = device.get('callback_url', '')

        if not ip or ip == 'YOUR_DEVICE_IP' or not callback_url or callback_url == 'http://YOUR_SERVER_IP:8000/api/v1/handheld-callback/':
            return

        base_url = f'http://{ip}:{port}'
        try:
            logger.info('[启动] 注册手持终端回调地址: %s', callback_url)
            resp = requests.post(
                f'{base_url}/setIdentifyCallBack',
                data={'pass': password, 'callbackUrl': callback_url},
                timeout=10,
            )
            logger.info('[启动] 回调注册结果: HTTP %d %s', resp.status_code, resp.text.strip()[:100])
        except Exception as e:
            logger.warning('[启动] 回调注册失败: %s', e)
