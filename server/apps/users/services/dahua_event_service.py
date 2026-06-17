import asyncio
import json
import logging
import re
import threading
import time
import requests
import yaml
import os
from django.conf import settings

logger = logging.getLogger(__name__)


class DahuaEventService:
    """大华门禁事件订阅服务 - 后端启动时自动连接"""

    _thread = None
    _running = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._thread = threading.Thread(target=cls._run, daemon=True)
        cls._thread.start()
        logger.info('大华事件订阅服务已启动')

    @classmethod
    def _load_config(cls):
        config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('dahua', {})

    @classmethod
    def _parse_event(cls, raw_text):
        """解析单个事件文本，提取 Code、action 和 JSON data"""
        raw_text = raw_text.strip()
        if not raw_text or raw_text == 'Heartbeat':
            return None

        # 跳过 Content-Type / Content-Length 等 HTTP 头
        lines = []
        skip_headers = True
        for line in raw_text.split('\n'):
            stripped = line.strip()
            if skip_headers:
                if stripped.lower().startswith('content-') or not stripped:
                    continue
                skip_headers = False
            lines.append(line)

        text = '\n'.join(lines).strip()
        if not text or text == 'Heartbeat':
            return None

        # 提取 Code、action
        header_match = re.match(r'Code=(?P<code>\w+);action=(?P<action>\w+);index=\d+;data=', text)
        if not header_match:
            return None

        code = header_match.group('code')
        action = header_match.group('action')

        # 提取 JSON 部分：从第一个 { 开始，用括号计数找到匹配的 }
        json_start = text.index('{')
        depth = 0
        json_end = -1
        for i in range(json_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    json_end = i + 1
                    break

        if json_end == -1:
            return None

        data_str = text[json_start:json_end]

        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            logger.warning(f'JSON解析失败: {data_str[:200]}')
            return None

        return {
            'code': code,
            'action': action,
            **data,
        }

    @classmethod
    def _broadcast(cls, event_data):
        """通过 Django Channels 广播事件到 WebSocket 客户端"""
        try:
            from apps.users.consumers import get_event_loop
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if not channel_layer:
                print('[广播] channel_layer 为 None')
                return

            loop = get_event_loop()
            if loop and loop.is_running():
                # 使用 Daphne 的事件循环调度广播，确保消息在同一事件循环内分发
                future = asyncio.run_coroutine_threadsafe(
                    channel_layer.group_send(
                        'door_events',
                        {
                            'type': 'door_event',
                            'data': event_data,
                        }
                    ),
                    loop
                )
                future.result(timeout=2)
                print(f'[广播] 已发送: {event_data.get("code", "unknown")}')
            else:
                print('[广播] 事件循环未就绪，无 WebSocket 客户端连接')
        except Exception as e:
            print(f'[广播] 失败: {e}')
            logger.error(f'广播事件失败: {e}')

    @classmethod
    def _run(cls):
        dahua_config = cls._load_config()
        username = dahua_config.get('userName', '')
        password = dahua_config.get('password', '')
        base_url = dahua_config.get('base_url', '').rstrip('/')
        url = f'{base_url}/cgi-bin/eventManager.cgi?action=attach&codes=[All]&heartbeat=5'

        if not base_url:
            logger.error('大华 base_url 未配置')
            return

        auth = requests.auth.HTTPDigestAuth(username, password) if username else None

        while cls._running:
            try:
                logger.info(f'正在连接大华事件订阅: {url}')
                resp = requests.get(url, auth=auth, stream=True, timeout=(10, None))
                logger.info(f'事件订阅连接成功, status={resp.status_code}')

                buffer = ''
                for chunk in resp.iter_content(chunk_size=1024):
                    if not cls._running:
                        break
                    if not chunk:
                        continue

                    buffer += chunk.decode('utf-8', errors='ignore')

                    # 按 boundary 分割
                    while '--myboundary' in buffer:
                        parts = buffer.split('--myboundary', 1)
                        part = parts[0]
                        buffer = parts[1] if len(parts) > 1 else ''

                        event = cls._parse_event(part)
                        if event:
                            print(f'[大华事件] {event["code"]}: {json.dumps(event, ensure_ascii=False)}')
                            logger.info(f'[大华事件] {event["code"]}: {json.dumps(event, ensure_ascii=False)}')
                            cls._broadcast(event)

            except requests.RequestException as e:
                logger.error(f'事件订阅连接断开: {e}, 5秒后重连...')
                time.sleep(5)
