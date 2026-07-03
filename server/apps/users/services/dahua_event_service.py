import asyncio
import base64
import hashlib
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
    """大华门禁事件订阅服务 - 后端启动时自动连接两台设备"""

    _threads = []
    _running = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True

        # 罪犯人脸识别事件（192.168.100.108）
        t1 = threading.Thread(target=cls._run_door_event, daemon=True)
        t1.start()

        # 民警/特警人脸抓拍事件（192.168.100.155）
        t2 = threading.Thread(target=cls._run_smart_event, daemon=True)
        t2.start()

        cls._threads = [t1, t2]
        logger.info('大华事件订阅服务已启动（双设备）')

    @classmethod
    def _load_config(cls):
        config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

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
    def _parse_kv_event(cls, text):
        """解析大华智能事件的 key-value 格式元数据。

        格式示例:
            Events[0].Code=AccessControl
            Events[0].Data.UserID=2
            Events[0].Data.Similarity=99
        """
        kv = {}
        for line in text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, val = line.split('=', 1)
                kv[key.strip()] = val.strip()

        if not kv:
            return None

        code = kv.get('Events[0].Code', '')
        if not code:
            return None

        event = {
            'code': code,
            'action': kv.get('Events[0].Action', 'Pulse'),
        }

        # 提取 Events[0].Data.* 字段
        for k, v in kv.items():
            prefix = 'Events[0].Data.'
            if k.startswith(prefix):
                field = k[len(prefix):]
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                event[field] = v

        return event

    @classmethod
    def _parse_section(cls, header_part, body):
        """解析单个 section（header + body），返回事件 dict 或 None。"""
        # 解析 headers
        content_type = ''
        for line in header_part.split('\n'):
            line = line.strip()
            if line.lower().startswith('content-type:'):
                content_type = line.split(':', 1)[1].strip().lower()

        if 'image' in content_type or 'octet' in content_type:
            image_data = body.encode('latin-1') if isinstance(body, str) else body
            if image_data:
                print(f'[解析] 图片: {len(image_data)} bytes')
                return {'_image_data': image_data}
        else:
            text = body.strip()
            if text and text != 'Heartbeat':
                event = cls._parse_event(text)
                if not event:
                    event = cls._parse_kv_event(text)
                if event:
                    print(f'[解析] 元数据: code={event.get("code")}')
                    return event
        return None

    @classmethod
    def _broadcast(cls, event_data):
        """通过 Django Channels 广播事件到 WebSocket 客户端"""
        try:
            from apps.users.consumers import get_event_loop
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            loop = get_event_loop()
            if loop and loop.is_running():
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
                code = event_data.get('code', 'unknown')
                event_type = event_data.get('type', 'unknown')
                print(f'[广播] 已发送: type={event_type} code={code}')
            else:
                print('[广播] 事件循环未就绪，无 WebSocket 客户端连接')
        except Exception as e:
            print(f'[广播] 失败: {e}')
            logger.error(f'广播事件失败: {e}')

    @classmethod
    def _run_door_event(cls):
        """罪犯人脸识别事件订阅（192.168.100.108）"""
        config = cls._load_config()
        dahua = config.get('dahua', {})
        username = dahua.get('userName', '')
        password = dahua.get('password', '')
        base_url = dahua.get('base_url', '').rstrip('/')

        if not base_url:
            logger.error('大华 base_url 未配置')
            return

        url = f'{base_url}/cgi-bin/eventManager.cgi?action=attach&codes=[All]&heartbeat=5'
        auth = requests.auth.HTTPDigestAuth(username, password) if username else None

        while cls._running:
            try:
                resp = requests.get(url, auth=auth, stream=True, timeout=(10, None))
                logger.info(f'[门禁事件] 连接成功, status={resp.status_code}')

                buffer = ''
                for chunk in resp.iter_content(chunk_size=1024):
                    if not cls._running:
                        break
                    if not chunk:
                        continue

                    buffer += chunk.decode('utf-8', errors='ignore')

                    while '--myboundary' in buffer:
                        parts = buffer.split('--myboundary', 1)
                        part = parts[0]
                        buffer = parts[1] if len(parts) > 1 else ''

                        event = cls._parse_event(part)
                        if event:
                            event['type'] = 'door'
                            cls._broadcast(event)

            except requests.RequestException as e:
                logger.error(f'[门禁事件] 连接断开: {e}, 5秒后重连...')
                time.sleep(5)

    @classmethod
    def _read_line(cls, raw, buf):
        """从流中读取一行，返回 (行内容, 剩余buffer)"""
        while b'\n' not in buf:
            chunk = raw.read(512)
            if not chunk:
                return None, buf
            buf += chunk
        line, buf = buf.split(b'\n', 1)
        return line.rstrip(b'\r'), buf

    @classmethod
    def _read_bytes(cls, raw, length, buf):
        """从流中精确读取指定字节数"""
        while len(buf) < length:
            need = length - len(buf)
            chunk = raw.read(min(need, 65536))
            if not chunk:
                break
            buf += chunk
        return buf[:length], buf[length:]

    @classmethod
    def _run_smart_event(cls):
        """民警/特警人脸抓拍智能事件订阅（192.168.100.155）"""
        config = cls._load_config()
        dahua = config.get('dahua', {})
        smart = config.get('dahua_smart', {})
        username = smart.get('userName', dahua.get('userName', ''))
        password = smart.get('password', dahua.get('password', ''))
        base_url = smart.get('base_url', '').rstrip('/')


        if not base_url:
            print('[智能事件] 错误: base_url 未配置')
            return

        url = f'{base_url}/cgi-bin/snapManager.cgi'
        params = {
            'action': 'attachFileProc',
            'Flags[0]': 'Event',
            'Events': '[AccessControl]',
            'heartbeat': 5,
        }
        auth = requests.auth.HTTPDigestAuth(username, password) if username else None

        while cls._running:
            try:
                resp = requests.get(url, params=params, auth=auth, stream=True, timeout=(10, 120))
                print(f'[智能事件] 连接成功, status={resp.status_code}')

                if resp.status_code != 200:
                    time.sleep(5)
                    continue

                # 从 Content-Type 提取 boundary
                content_type = resp.headers.get('Content-Type', '')
                boundary_match = re.search(r'boundary=(.+)', content_type)
                if not boundary_match:
                    time.sleep(5)
                    continue
                boundary = boundary_match.group(1).strip()

                raw = resp.raw
                buf = b''
                event_user_id = ''
                event_user_name = ''

                while cls._running:
                    # 读一行
                    line, buf = cls._read_line(raw, buf)
                    if line is None:
                        break

                    line_str = line.decode('utf-8', errors='replace').strip()

                    # 跳过 boundary 行和空行
                    if not line_str or boundary in line_str or line_str == '--':
                        continue

                    # 这是 header 行，继续读完整个 header
                    header_lines = [line_str]
                    while True:
                        hline, buf = cls._read_line(raw, buf)
                        if hline is None:
                            break
                        hline_str = hline.decode('utf-8', errors='replace').strip()
                        if not hline_str:  # 空行 = header 结束
                            break
                        header_lines.append(hline_str)

                    header = '\n'.join(header_lines)

                    ct_match = re.search(r'Content-Type:\s*(.+)', header, re.IGNORECASE)
                    ct = ct_match.group(1).strip() if ct_match else 'unknown'

                    cl_match = re.search(r'Content-Length:\s*(\d+)', header, re.IGNORECASE)
                    cl = int(cl_match.group(1)) if cl_match else 0

                    if cl == 0:
                        continue

                    if 'image' in ct.lower():
                        # 精确读取图片数据
                        body, buf = cls._read_bytes(raw, cl, buf)
                        image_b64 = base64.b64encode(body).decode('ascii')
                        broadcast_data = {'type': 'face', 'code': 'SnapPic', 'image_base64': image_b64}
                        if event_user_name:
                            broadcast_data['user_name'] = event_user_name
                        if event_user_id:
                            broadcast_data['user_id'] = event_user_id
                        cls._broadcast(broadcast_data)
                        # 重置，等待下一组事件
                        event_user_id = ''
                        event_user_name = ''

                    elif 'text' in ct.lower() or 'plain' in ct.lower():
                        # 精确读取文本数据
                        body, buf = cls._read_bytes(raw, cl, buf)
                        body_text = body.decode('utf-8', errors='replace').strip()

                        if body_text == 'Heartbeat':
                            print(f'[智能事件] 心跳')
                        else:
                            print(f'[智能事件] 收到事件文本:')
                            for eline in body_text.split('\n'):
                                eline = eline.strip()
                                if eline:
                                    print(f'  {eline}')
                                if '.UserID=' in eline:
                                    event_user_id = eline.split('=', 1)[1].strip()
                                if '.Name=' in eline:
                                    event_user_name = eline.split('=', 1)[1].strip()
                                if '.CardName=' in eline:
                                    event_user_name = eline.split('=', 1)[1].strip()
                            print(f'[智能事件] 解析结果: UserID={event_user_id}, Name={event_user_name}')

            except requests.RequestException as e:
                time.sleep(5)
            except Exception as e:
                time.sleep(5)
