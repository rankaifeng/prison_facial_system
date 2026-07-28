#!/usr/bin/env python3
"""
WebSocket + HTTP 测试服务器

功能：
  1. WebSocket 服务（端口 9000）：处理一体机长连接、declare/ping/addUser 下发
  2. HTTP POST 服务（端口 9001）：接收一体机识别记录上传 /api/v1/record/face
     - 解析 photo (base64) 和 user_id
     - 照片存到 ./recognition_logs/yyyy-mm-dd/hh-mm-ss_<user_id>.jpg
     - 返回 {"Result": 0, "Msg": ""}

依赖：
  pip install websockets

用法：
  python3 ws_test_server.py

一体机配置：
  WebSocket 服务器：ws://<本机IP>:9000
  HTTP 服务器（识别记录）：http://<本机IP>:9001

按 Ctrl+C 退出
"""
import asyncio
import json
import socket
import sys
import os
import base64
import urllib.parse
import argparse
from datetime import datetime

try:
    import websockets
except ImportError:
    print('错误：未安装 websockets，请先执行：pip install websockets')
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
            if ':' not in ip and ip not in ips:  # 只显示 IPv4
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
}

# 当前在线设备：device_no -> client_ip
online_devices = {}


async def send_test_add_user(websocket, device_no, client_id):
    """设备 declare 成功后，5 秒自动下发一条测试 addUser 指令"""
    await asyncio.sleep(5)
    test_user = {
        'cmd': 'to_device',
        'from': client_id,
        'to': device_no,
        'extra': 'test_extra_001',
        'data': {
            'cmd': 'addUser',
            'user_id': 'TEST001',
            'name': '测试用户',
            'id_card': '',
            # face_template 先留空，看设备是否要求必传
            # 如果设备返回 "face_template 必传" 之类的错误，再补一张测试照片
            'face_template': '',
            'id_valid': '2030-12-31',
            'user_type': 0,
            'mode': '0',
        }
    }
    print(f'\n[{now()}] 🔧 自动下发测试 addUser：')
    print(f'          user_id=TEST001, name=测试用户')
    print(f'          face_template=空（测试设备是否要求必传）')
    try:
        await websocket.send(json.dumps(test_user, ensure_ascii=False))
        print(f'          📤 已发送，等待设备返回 addUserRet...')
    except Exception as e:
        print(f'          ❌ 发送失败: {e}')


async def handler(websocket):
    client_addr = websocket.remote_address
    client_ip = client_addr[0] if client_addr else 'unknown'
    client_port = client_addr[1] if client_addr else 0

    stats['connections_total'] += 1
    print(f'\n[{now()}] ✅ 客户端连上来：{client_ip}:{client_port}')
    print(f'          (累计连接数: {stats["connections_total"]})')

    current_device_no = None

    try:
        async for message in websocket:
            stats['messages_total'] += 1
            print(f'\n[{now()}] 📥 收到来自 {client_ip} 的消息：')
            print(f'          原文: {message[:500]}{"..." if len(message) > 500 else ""}')

            # 尝试解析 JSON
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

            # 处理 declare（设备声明，文档里"设备端声明"对应这个 cmd）
            # 也兼容 register（某些版本可能用 register）
            if cmd in ('declare', 'register'):
                # declare 用 sn 作为设备编号，register 用 device_no
                device_no = data.get('sn', '') or data.get('device_no', '') or data.get('deviceNo', '')
                name = data.get('name', '') or data.get('type', '')
                device_ip = data.get('ip', client_ip)
                version = data.get('version_name', '') or data.get('version_code', '')
                current_device_no = device_no
                online_devices[device_no] = client_ip
                stats['register_count'] += 1

                print(f'          📋 设备注册：sn/device_no={device_no}, ip={device_ip}, version={version}')

                # 返回 client_id（文档要求"返回客户端连接的唯一标识 client_id"）
                # 用 declare_ack 作为回复 cmd（猜测格式，如果设备不认可以改成 declare_ret）
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

                # 设备声明成功后，5 秒自动下发一条测试 addUser
                asyncio.create_task(
                    send_test_add_user(websocket, device_no, client_id)
                )

            # 处理 heartbeat / ping（设备心跳）
            elif cmd in ('heartbeat', 'ping'):
                stats['heartbeat_count'] += 1
                device_no = data.get('sn', '') or data.get('device_no', current_device_no or '')
                ts = data.get('timestamp', '')
                print(f'          💓 心跳({cmd})：sn={device_no}, ts={ts}')

                # ping 用 pong 回复，heartbeat 用 heartbeat_ack
                if cmd == 'ping':
                    ack = {'cmd': 'pong', 'timestamp': int(datetime.now().timestamp())}
                else:
                    ack = {'cmd': 'heartbeat_ack', 'code': 0, 'msg': 'ok'}
                await websocket.send(json.dumps(ack, ensure_ascii=False))

            # 处理 to_client（设备回执，比如 addUserRet）
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

                # 模拟服务端记录，回个确认
                ack = {'cmd': 'reply_ack', 'code': 0, 'msg': '服务端已收到回执'}
                await websocket.send(json.dumps(ack, ensure_ascii=False))

            # 其他未知 cmd，原样 echo
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


async def print_stats_periodically():
    """每 30 秒打印一次统计"""
    while True:
        await asyncio.sleep(30)
        print(f'\n[{now()}] 📊 统计：连接 {stats["connections_total"]} | 消息 {stats["messages_total"]} | '
              f'注册 {stats["register_count"]} | 心跳 {stats["heartbeat_count"]} | '
              f'addUser回执 {stats["add_user_ret_count"]} | 在线设备 {len(online_devices)} | '
              f'识别记录 {stats.get("record_face_count", 0)}')


# ===========================================
# HTTP 部分：接收设备识别记录 /api/v1/record/face
# ===========================================

# 识别记录保存目录（脚本所在目录下的 recognition_logs/）
RECORD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognition_logs')


def decode_photo(photo_field):
    """
    按文档解码照片：
    1. UrlDecode UTF-8
    2. 去掉 data:image/jpeg;base64, 前缀
    3. base64 解码成图片字节
    返回 bytes，失败返回 None
    """
    if not photo_field:
        return None
    try:
        # 1. UrlDecode（如果被 urlencode 过的话）
        decoded_url = urllib.parse.unquote(photo_field)

        # 2. 去掉 base64 前缀
        if ',base64,' in decoded_url:
            b64_data = decoded_url.split(',base64,', 1)[1]
        elif decoded_url.startswith('data:image/') and ',' in decoded_url:
            b64_data = decoded_url.split(',', 1)[1]
        else:
            # 没有 data: 前缀，直接当 base64 处理
            b64_data = decoded_url

        # 3. base64 解码
        return base64.b64decode(b64_data)
    except Exception as e:
        print(f'          ⚠️ 照片解码失败: {e}')
        return None


def save_photo(photo_bytes, user_id, recog_time):
    """保存照片到 recognition_logs/yyyy-mm-dd/hh-mm-ss_<user_id>.jpg，返回相对路径"""
    try:
        # 解析识别时间作为文件名
        try:
            dt = datetime.strptime(recog_time, '%Y-%m-%d %H:%M:%S')
        except Exception:
            dt = datetime.now()

        date_dir = os.path.join(RECORD_DIR, dt.strftime('%Y-%m-%d'))
        os.makedirs(date_dir, exist_ok=True)

        filename = f'{dt.strftime("%H-%M-%S")}_{user_id}.jpg'
        filepath = os.path.join(date_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(photo_bytes)

        return filepath
    except Exception as e:
        print(f'          ⚠️ 照片保存失败: {e}')
        return None


async def process_record_face(body_bytes, client_ip):
    """处理 /api/v1/record/face 请求"""
    try:
        data = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        print(f'\n[{now()}] ❌ record/face JSON 解析失败: {e}')
        return {'Result': -1, 'Msg': 'JSON 解析失败'}

    sn = data.get('sn', '')
    count = data.get('Count', 0)
    logs = data.get('logs', []) or []

    print(f'\n[{now()}] 📸 收到识别记录：来自 {client_ip}, sn={sn}, Count={count}, logs={len(logs)}条')

    for i, log in enumerate(logs):
        user_id = log.get('user_id', '')
        recog_time = log.get('recog_time', '')
        recog_type = log.get('recog_type', '')
        user_name = log.get('user_name', '')
        confidence = log.get('confidence', '')
        photo_field = log.get('photo', '')
        body_temp = log.get('body_temperature', '')

        print(f'          [{i+1}] user_id={user_id}, name={user_name}, '
              f'time={recog_time}, type={recog_type}, confidence={confidence}, '
              f'temp={body_temp}, photo_len={len(photo_field) if photo_field else 0}')

        # 解码并保存照片
        if photo_field:
            photo_bytes = decode_photo(photo_field)
            if photo_bytes:
                filepath = save_photo(photo_bytes, user_id, recog_time)
                if filepath:
                    print(f'          ✅ 照片已保存: {filepath} ({len(photo_bytes)} bytes)')
                else:
                    print(f'          ❌ 照片保存失败')
            else:
                print(f'          ❌ 照片解码失败')
        else:
            print(f'          ⚠️ 本次记录无照片字段')

    stats['record_face_count'] = stats.get('record_face_count', 0) + len(logs)

    # 必须返回 Result=0，否则设备会每 2 分钟重试
    return {'Result': 0, 'Msg': ''}


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
            try:
                key, _, value = line.decode('utf-8', errors='ignore').partition(':')
                headers[key.strip().lower()] = value.strip()
            except Exception:
                continue

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
            result = await process_record_face(body, client_ip)
        elif method == 'GET' and path == '/':
            result = {'Result': 0, 'Msg': 'WS+HTTP 测试服务器运行中'}
        else:
            # 其他路径返回 404
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


async def main(port, http_port):
    ips = get_local_ips()

    print('=' * 70)
    print('  WebSocket + HTTP 测试服务器')
    print('=' * 70)
    print(f'  WebSocket 端口: ws://0.0.0.0:{port}        (设备 declare/心跳/addUser)')
    print(f'  HTTP 端口:      http://0.0.0.0:{http_port}  (设备上传识别记录)')
    print(f'  识别记录保存到: {RECORD_DIR}')
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

    # 启动统计任务
    asyncio.create_task(print_stats_periodically())

    # 同时启动 WebSocket 和 HTTP 服务
    ws_server = await websockets.serve(
        handler, '0.0.0.0', port,
        ping_interval=20, ping_timeout=60,
        server_header='WS-Test-Server/1.0',
    )
    http_server = await asyncio.start_server(handle_http, '0.0.0.0', http_port)

    await asyncio.Future()  # 永远阻塞


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WebSocket + HTTP 测试服务器')
    parser.add_argument('--port', type=int, default=9000, help='WebSocket 监听端口，默认 9000')
    parser.add_argument('--http-port', type=int, default=9001, help='HTTP 监听端口，默认 9001')
    args = parser.parse_args()

    # 抑制 websockets 库的握手失败 traceback（POST 探测会刷屏，但其实是无害的）
    import logging
    logging.getLogger('websockets.server').setLevel(logging.CRITICAL)
    logging.getLogger('websockets.protocol').setLevel(logging.CRITICAL)
    logging.getLogger('websockets.asyncio.server').setLevel(logging.CRITICAL)

    try:
        asyncio.run(main(args.port, args.http_port))
    except KeyboardInterrupt:
        print('\n\n再见！')
        sys.exit(0)
