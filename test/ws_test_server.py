#!/usr/bin/env python3
"""
WebSocket + HTTP 测试服务器

核心业务只有两个方法：
  1. send_users_to_device  - 设备 declare 成功后，批量下发测试人员信息
  2. handle_record_face    - 接收设备识别成功记录，打印人员信息和识别信息

服务端口：
  WebSocket 端口 9000：设备 declare/心跳/addUserRet
  HTTP 端口 9001：设备上传识别记录 /api/v1/record/face

依赖：
  pip install websockets

用法：
  python3 ws_test_server.py
  python3 ws_test_server.py --add-user-count 50

一体机配置：
  WebSocket 服务器：ws://<本机IP>:9000
  HTTP 识别记录接口：http://<本机IP>:9001/api/v1/record/face

按 Ctrl+C 退出
"""
import asyncio
import json
import socket
import sys
import os
import io
import base64
import urllib.parse
import argparse
from datetime import datetime

try:
    import websockets
except ImportError:
    print('错误：未安装 websockets，请先执行：pip install websockets')
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print('错误：未安装 Pillow，请先执行：pip install Pillow')
    sys.exit(1)


def now():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]


def get_local_ips():
    """获取本机所有 IP，方便用户配置一体机"""
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ':' not in ip and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips or ['127.0.0.1']


# 统计
stats = {
    'connections_total': 0,
    'messages_total': 0,
    'register_count': 0,
    'heartbeat_count': 0,
    'add_user_ret_count': 0,
    'record_face_count': 0,
}

# 当前在线设备：device_no -> client_ip
online_devices = {}

# 设备 declare 后批量下发的测试人员数量（由命令行参数 --add-user-count 设置，默认 10）
ADD_USER_COUNT = 10

# 人脸模板图片路径（下发人员时用这张图的 base64 作为 face_template）
FACE_IMAGE_PATH = '~/Desktop/facejpg'


def load_face_template(image_path):
    """按设备厂商规范处理人脸图片：
    1. 压缩成 jpg，大小不超过 300KB，尺寸不超过 1280*720
    2. 转 base64 并加前缀 data:image/jpeg;base64,
    3. 对完整字符串做 UrlEncode UTF-8 编码
    """
    expanded_path = os.path.expanduser(image_path)
    if not os.path.exists(expanded_path):
        print(f'\n[{now()}] ❌ 人脸图片不存在: {expanded_path}')
        return None
    try:
        with Image.open(expanded_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 尺寸不超过 1280*720，按比例缩放
            max_w, max_h = 1280, 720
            w, h = img.size
            if w > max_w or h > max_h:
                ratio = min(max_w / w, max_h / h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

            # 迭代降低质量，直到大小 <= 300KB
            quality = 85
            data = None
            while quality >= 10:
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=quality)
                data = buf.getvalue()
                if len(data) <= 300 * 1024:
                    break
                quality -= 10

            # 转 base64 并加前缀
            b64 = base64.b64encode(data).decode('utf-8')
            data_uri = f'data:image/jpeg;base64,{b64}'

            # UrlEncode UTF-8 编码（所有特殊字符都编码）
            encoded = urllib.parse.quote(data_uri, safe='')

            print(f'\n[{now()}] 📷 人脸图片处理完成:')
            print(f'          原始: {expanded_path} ({os.path.getsize(expanded_path)} bytes, {w}x{h})')
            print(f'          压缩: {len(data)} bytes, quality={quality}, 尺寸={img.size[0]}x{img.size[1]}')
            print(f'          编码: base64 长度={len(b64)}, UrlEncode 后长度={len(encoded)}')
            return encoded
    except Exception as e:
        print(f'\n[{now()}] ❌ 人脸图片处理失败: {e}')
        return None


# ===========================================
# 核心方法 1：下发人员信息到设备
# ===========================================
async def send_users_to_device(websocket, device_no, client_id, count, interval=1.5):
    """设备 declare 成功后，批量下发多条测试 addUser 指令，模拟真实环境"""
    await asyncio.sleep(5)

    # 读取本地图片转 base64 作为人脸模板
    face_template = load_face_template(FACE_IMAGE_PATH)
    if not face_template:
        print(f'\n[{now()}] ❌ 人脸模板加载失败，终止下发')
        return

    print(f'\n[{now()}] 🔧 开始批量下发 {count} 条测试人员到设备 {device_no}')
    print(f'          人脸模板: {os.path.expanduser(FACE_IMAGE_PATH)} (base64 长度={len(face_template)})')
    print(f'          每条间隔 {interval} 秒')

    success_count = 0
    fail_count = 0

    for i in range(1, count + 1):
        user_id = f'TEST{i:03d}'
        message = {
            'cmd': 'to_device',
            'from': client_id,
            'to': device_no,
            'extra': f'test_extra_{i:03d}',
            'data': {
                'cmd': 'addUser',
                'user_id': user_id,
                'name': f'测试用户{i}',
                'id_card': '',
                'face_template': face_template,
                'id_valid': '2030-12-31',
                'user_type': 0,
                'mode': '0',
            }
        }
        try:
            await websocket.send(json.dumps(message, ensure_ascii=False))
            success_count += 1
            print(f'          [{i}/{count}] 📤 已下发 user_id={user_id} name=测试用户{i}')
        except Exception as e:
            fail_count += 1
            print(f'          [{i}/{count}] ❌ 下发失败 user_id={user_id}: {e}')

        if i < count:
            await asyncio.sleep(interval)

    print(f'\n[{now()}] ✅ 批量下发完成：成功 {success_count} 条，失败 {fail_count} 条')
    print(f'          等待设备返回 addUserRet 回执...')


# ===========================================
# 核心方法 2：接收设备识别成功记录
# ===========================================
GENDER_MAP = {0: '男', 1: '女', -1: '未知'}
PASS_STATUS_MAP = {0: '已开门', 1: '未开门', 2: '未开门(关联识别)'}
ALCOHOL_PASS_MAP = {0: '合格', 1: '异常'}


async def handle_record_face(body_bytes, client_ip):
    """处理 /api/v1/record/face 请求，打印识别信息

    始终返回 Result=0，设备收到后才会删除本地记录，否则会每 2 分钟重试。
    """
    try:
        data = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        print(f'\n[{now()}] ❌ record/face JSON 解析失败: {e}')
        return {'Result': 0, 'Msg': ''}

    sn = data.get('sn', '')
    logs = data.get('logs', []) or []

    print(f'\n{"="*70}')
    print(f'[{now()}] 📸 收到识别记录  来源={client_ip}  sn={sn}  记录数={len(logs)}')
    print(f'{"="*70}')

    for i, log in enumerate(logs):
        gender = log.get('gender', '')
        pass_status = log.get('pass_status', '')
        alcohol_pass = log.get('alcohol_pass', '')
        location = log.get('location', {}) or {}

        print(f'\n  ---- 记录 [{i+1}/{len(logs)}] ----')
        print(f'  👤 人员:  user_id={log.get("user_id","")}  name={log.get("user_name","")}  '
              f'gender={GENDER_MAP.get(gender, gender)}  user_type={log.get("user_type","")}')
        print(f'  🕐 时间:  {log.get("recog_time","")}')
        print(f'  📌 类型:  {log.get("recog_type","")}    🚪 开门: {PASS_STATUS_MAP.get(pass_status, pass_status)}    '
              f'📊 置信度: {log.get("confidence","")}')
        print(f'  🌡 体温: {log.get("body_temperature","")}℃  室温: {log.get("room_temperature","")}℃  '
              f'反射率: {log.get("reflectivity","")}')
        if log.get('card_number'):
            print(f'  💳 卡号:  {log["card_number"]}')
        if log.get('alcohol_result') or alcohol_pass != '':
            print(f'  🍺 酒精:  数值={log.get("alcohol_result","")}  结果={ALCOHOL_PASS_MAP.get(alcohol_pass, alcohol_pass)}')
        if location:
            print(f'  📍 位置:  经度={location.get("longitude","")}  纬度={location.get("latitude","")}  '
                  f'地址={location.get("address","")}')
        if log.get('extra'):
            print(f'  📎 extra: {log["extra"]}')
        if log.get('photo'):
            print(f'  📷 识别照片: base64 长度={len(log["photo"])}')
        if log.get('panoramic_picture'):
            print(f'  📷 抓拍照:   base64 长度={len(log["panoramic_picture"])}')

    print(f'\n{"="*70}')

    stats['record_face_count'] += len(logs)
    return {'Result': 0, 'Msg': ''}


# ===========================================
# WebSocket 处理器：设备连接、declare、心跳、回执
# ===========================================
async def handler(websocket):
    client_addr = websocket.remote_address
    client_ip = client_addr[0] if client_addr else 'unknown'
    client_port = client_addr[1] if client_addr else 0

    stats['connections_total'] += 1
    print(f'\n[{now()}] ✅ 客户端连上来：{client_ip}:{client_port}')

    current_device_no = None

    try:
        async for message in websocket:
            stats['messages_total'] += 1
            print(f'\n[{now()}] 📥 收到来自 {client_ip} 的消息：')
            print(f'          原文: {message[:500]}{"..." if len(message) > 500 else ""}')

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print(f'          ⚠️ 非 JSON 格式，原样 echo 回去')
                try:
                    await websocket.send(message)
                except Exception as e:
                    print(f'          ❌ echo 失败: {e}')
                continue

            cmd = data.get('cmd', '')
            print(f'          解析: cmd={cmd}')

            # 设备声明
            if cmd in ('declare', 'register'):
                device_no = data.get('sn', '') or data.get('device_no', '') or data.get('deviceNo', '')
                device_ip = data.get('ip', client_ip)
                version = data.get('version_name', '') or data.get('version_code', '')
                current_device_no = device_no
                online_devices[device_no] = client_ip
                stats['register_count'] += 1

                print(f'          📋 设备注册：sn={device_no}, ip={device_ip}, version={version}')

                client_id = f'server_{int(datetime.now().timestamp() * 1000)}'
                ack = {
                    'cmd': 'declare_ack',
                    'client_id': client_id,
                    'sn': device_no,
                    'code': 0,
                    'msg': '声明成功',
                }
                await websocket.send(json.dumps(ack, ensure_ascii=False))
                print(f'          📤 已回复 declare_ack，client_id={client_id}')

                # 设备声明成功后，5 秒自动批量下发测试人员
                asyncio.create_task(
                    send_users_to_device(websocket, device_no, client_id, count=ADD_USER_COUNT)
                )

            # 心跳
            elif cmd in ('heartbeat', 'ping'):
                stats['heartbeat_count'] += 1
                device_no = data.get('sn', '') or data.get('device_no', current_device_no or '')
                ts = data.get('timestamp', '')
                print(f'          💓 心跳({cmd})：sn={device_no}, ts={ts}')

                if cmd == 'ping':
                    ack = {'cmd': 'pong', 'timestamp': int(datetime.now().timestamp())}
                else:
                    ack = {'cmd': 'heartbeat_ack', 'code': 0, 'msg': 'ok'}
                await websocket.send(json.dumps(ack, ensure_ascii=False))

            # 设备回执（addUserRet 等）
            elif cmd == 'to_client':
                inner = data.get('data', {}) or {}
                inner_cmd = inner.get('cmd', '')
                user_id = inner.get('user_id', '')
                code = inner.get('code', '')
                msg = inner.get('msg', '')

                if inner_cmd == 'addUserRet':
                    stats['add_user_ret_count'] += 1
                    status = '✅ 成功' if code == 0 else f'❌ 失败(code={code})'
                    print(f'          📤 addUser 回执：user_id={user_id} {status} msg={msg}')
                else:
                    print(f'          📤 回执：{inner_cmd} user_id={user_id} code={code} msg={msg}')

                ack = {'cmd': 'reply_ack', 'code': 0, 'msg': '服务端已收到回执'}
                await websocket.send(json.dumps(ack, ensure_ascii=False))

            # 未知 cmd，原样 echo
            else:
                print(f'          ❓ 未知 cmd={cmd}，原样 echo')
                await websocket.send(message)

    except websockets.exceptions.ConnectionClosed as e:
        print(f'\n[{now()}] ❌ 客户端断开：{client_ip} (code={e.code}, reason={e.reason})')
    except Exception as e:
        print(f'\n[{now()}] ❌ 异常：{type(e).__name__}: {e}')
    finally:
        if current_device_no and online_devices.get(current_device_no) == client_ip:
            online_devices.pop(current_device_no, None)
        print(f'          当前在线设备: {online_devices or "无"}')


# ===========================================
# HTTP 处理器：接收识别记录
# ===========================================
async def handle_http(reader, writer):
    """处理 HTTP 请求（仅处理 POST /api/v1/record/face）"""
    client_addr = writer.get_extra_info('peername')
    client_ip = client_addr[0] if client_addr else 'unknown'

    try:
        # 读取请求行
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            return
        parts = request_line.decode('utf-8', errors='ignore').strip().split()
        if len(parts) != 3:
            writer.close()
            return
        method, path, _ = parts

        # 读取 headers
        headers = {}
        while True:
            line = await reader.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            key, _, value = line.decode('utf-8', errors='ignore').partition(':')
            headers[key.strip().lower()] = value.strip()

        # 读取 body
        content_length = int(headers.get('content-length', 0))
        body = b''
        while len(body) < content_length:
            chunk = await reader.read(content_length - len(body))
            if not chunk:
                break
            body += chunk

        # 路由
        if method == 'POST' and path == '/api/v1/record/face':
            try:
                result = await handle_record_face(body, client_ip)
            except Exception as e:
                import traceback
                print(f'\n[{now()}] ❌ record/face 处理异常: {type(e).__name__}: {e}')
                traceback.print_exc()
                result = {'Result': 0, 'Msg': ''}
        elif method == 'GET' and path == '/':
            result = {'Result': 0, 'Msg': 'WS+HTTP 测试服务器运行中'}
        else:
            response = json.dumps({'error': 'not found'}).encode('utf-8')
            writer.write(b'HTTP/1.1 404 Not Found\r\n')
            writer.write(b'Content-Type: application/json\r\n')
            writer.write(f'Content-Length: {len(response)}\r\n'.encode())
            writer.write(b'Connection: close\r\n\r\n')
            writer.write(response)
            await writer.drain()
            writer.close()
            return

        # 返回响应
        response_body = json.dumps(result, ensure_ascii=False).encode('utf-8')
        writer.write(b'HTTP/1.1 200 OK\r\n')
        writer.write(b'Content-Type: application/json\r\n')
        writer.write(f'Content-Length: {len(response_body)}\r\n'.encode())
        writer.write(b'Connection: close\r\n\r\n')
        writer.write(response_body)
        await writer.drain()

    except Exception as e:
        print(f'\n[{now()}] ❌ HTTP 处理异常: {type(e).__name__}: {e}')
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def print_stats_periodically():
    """每 30 秒打印一次统计"""
    while True:
        await asyncio.sleep(30)
        print(f'\n[{now()}] 📊 统计：连接 {stats["connections_total"]} | 消息 {stats["messages_total"]} | '
              f'注册 {stats["register_count"]} | 心跳 {stats["heartbeat_count"]} | '
              f'addUser回执 {stats["add_user_ret_count"]} | 在线设备 {len(online_devices)} | '
              f'识别记录 {stats["record_face_count"]}')


async def main(port, http_port, add_user_count):
    global ADD_USER_COUNT
    ADD_USER_COUNT = add_user_count

    ips = get_local_ips()

    print('=' * 70)
    print('  WebSocket + HTTP 测试服务器')
    print('=' * 70)
    print(f'  WebSocket 端口: ws://0.0.0.0:{port}        (设备 declare/心跳/下发人员)')
    print(f'  HTTP 端口:      http://0.0.0.0:{http_port}  (设备上传识别记录)')
    print(f'  设备 declare 后自动下发: {ADD_USER_COUNT} 条测试人员')
    print(f'  启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    print('  本机 IP 地址（在一体机里配置其中一个）：')
    for ip in ips:
        print(f'    👉 ws://{ip}:{port}  /  http://{ip}:{http_port}')
    print()
    print('  一体机配置：')
    print(f'    WebSocket 服务器: ws://<IP>:{port}')
    print(f'    HTTP 识别记录接口: http://<IP>:{http_port}/api/v1/record/face')
    print()
    print('  按 Ctrl+C 退出')
    print('=' * 70)
    print(f'\n[{now()}] 等待设备连接和识别记录...\n')

    asyncio.create_task(print_stats_periodically())

    await websockets.serve(
        handler, '0.0.0.0', port,
        ping_interval=20, ping_timeout=60,
        server_header='WS-Test-Server/1.0',
    )
    await asyncio.start_server(handle_http, '0.0.0.0', http_port)

    await asyncio.Future()  # 永远阻塞


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WebSocket + HTTP 测试服务器')
    parser.add_argument('--port', type=int, default=9000, help='WebSocket 监听端口，默认 9000')
    parser.add_argument('--http-port', type=int, default=9001, help='HTTP 监听端口，默认 9001')
    parser.add_argument('--add-user-count', type=int, default=10,
                        help='设备 declare 后批量下发的测试人员数量，默认 10')
    args = parser.parse_args()

    # 抑制 websockets 库的握手失败 traceback（POST 探测会刷屏，但其实是无害的）
    import logging
    logging.getLogger('websockets.server').setLevel(logging.CRITICAL)
    logging.getLogger('websockets.protocol').setLevel(logging.CRITICAL)
    logging.getLogger('websockets.asyncio.server').setLevel(logging.CRITICAL)

    try:
        asyncio.run(main(args.port, args.http_port, args.add_user_count))
    except KeyboardInterrupt:
        print('\n\n再见！')
        sys.exit(0)
