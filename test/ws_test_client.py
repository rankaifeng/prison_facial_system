#!/usr/bin/env python3
"""
WebSocket 测试客户端 - 模拟一体机连接服务端

用途：
  模拟一体机的行为，连到 ws_test_server.py 或你的后端 WS 服务，
  验证服务端是否能正确接收 register / heartbeat / addUserRet。

依赖：
  pip install websockets

用法：
  # 连本机的测试服务端
  python3 ws_test_client.py --device TEST001

  # 连你后端的真实 WS 服务（要先实现 DeviceConsumer）
  python3 ws_test_client.py --device D001 --url ws://10.2.48.86:8000/ws/device/

  # 收到 addUser 后自动回成功
  python3 ws_test_client.py --device D001 --auto-reply

按 Ctrl+C 退出
"""
import asyncio
import json
import sys
import argparse
import random
from datetime import datetime

try:
    import websockets
except ImportError:
    print('错误：未安装 websockets，请先执行：pip install websockets')
    sys.exit(1)


def now():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]


async def main(url, device_no, name, auto_reply, fail_rate):
    print('=' * 70)
    print('  WebSocket 测试客户端（模拟一体机）')
    print('=' * 70)
    print(f'  服务端地址: {url}')
    print(f'  设备编号:   {device_no}')
    print(f'  设备名称:   {name or "(空)"}')
    print(f'  自动回执:   {"是" if auto_reply else "否"}')
    print(f'  失败概率:   {fail_rate * 100:.0f}%')
    print('=' * 70)
    print(f'\n[{now()}] 正在连接 {url} ...\n')

    retry_count = 0
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=60) as ws:
                print(f'[{now()}] ✅ 连接成功')
                retry_count = 0

                # 1. 发送 register
                register_msg = {
                    'cmd': 'register',
                    'device_no': device_no,
                    'name': name,
                }
                await ws.send(json.dumps(register_msg, ensure_ascii=False))
                print(f'[{now()}] 📤 发送 register: {register_msg}')

                # 2. 启动心跳任务
                async def heartbeat_loop():
                    while True:
                        await asyncio.sleep(30)
                        try:
                            hb = {'cmd': 'heartbeat', 'device_no': device_no}
                            await ws.send(json.dumps(hb, ensure_ascii=False))
                            print(f'[{now()}] 💓 发送心跳')
                        except Exception as e:
                            print(f'[{now()}] ⚠️ 心跳发送失败: {e}')
                            return

                hb_task = asyncio.create_task(heartbeat_loop())

                # 3. 接收消息循环
                async for message in ws:
                    print(f'\n[{now()}] 📥 收到: {message[:1000]}{"..." if len(message) > 1000 else ""}')

                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        print(f'          ⚠️ 非 JSON，忽略')
                        continue

                    cmd = data.get('cmd', '')

                    # 收到 register_ack
                    if cmd == 'register_ack':
                        client_id = data.get('client_id', '')
                        print(f'          ✅ 注册成功，client_id={client_id}')

                    # 收到 heartbeat_ack
                    elif cmd == 'heartbeat_ack':
                        print(f'          ✅ 心跳已确认')

                    # 收到 reply_ack
                    elif cmd == 'reply_ack':
                        pass  # 静默处理

                    # 收到 to_device（服务端下发指令）
                    elif cmd == 'to_device':
                        inner = data.get('data', {}) or {}
                        inner_cmd = inner.get('cmd', '')
                        from_field = data.get('from', '')  # 服务端的 client_id
                        to_field = data.get('to', '')  # 应该是自己 device_no

                        print(f'          📋 服务端下发: {inner_cmd}')
                        print(f'          from={from_field}, to={to_field}')

                        if inner_cmd == 'addUser':
                            user_id = inner.get('user_id', '')
                            user_name = inner.get('name', '')
                            print(f'          👤 addUser: user_id={user_id}, name={user_name}')

                            if auto_reply:
                                # 模拟设备处理，按 fail_rate 概率返回失败
                                if random.random() < fail_rate:
                                    code = random.choice([11, 12, 13, 14, 15])
                                    msg = f'模拟失败: 人脸质量错误 code={code}'
                                else:
                                    code = 0
                                    msg = '成功'

                                # 构造 addUserRet 回执
                                ret = {
                                    'cmd': 'to_client',
                                    'from': device_no,
                                    'to': from_field,  # 原样回传服务端的 from
                                    'data': {
                                        'cmd': 'addUserRet',
                                        'user_id': user_id,
                                        'code': code,
                                        'msg': msg,
                                    }
                                }
                                # 模拟设备处理耗时
                                await asyncio.sleep(random.uniform(0.1, 0.5))
                                await ws.send(json.dumps(ret, ensure_ascii=False))
                                status = '✅' if code == 0 else '❌'
                                print(f'          📤 已回执: {status} code={code} msg={msg}')

                        elif inner_cmd == 'deleteUser':
                            user_id = inner.get('user_id', '')
                            print(f'          🗑 deleteUser: user_id={user_id}')
                            if auto_reply:
                                ret = {
                                    'cmd': 'to_client',
                                    'from': device_no,
                                    'to': from_field,
                                    'data': {
                                        'cmd': 'deleteUserRet',
                                        'user_id': user_id,
                                        'code': 0,
                                        'msg': '成功',
                                    }
                                }
                                await ws.send(json.dumps(ret, ensure_ascii=False))
                                print(f'          📤 已回执 deleteUserRet')

                        else:
                            print(f'          ❓ 未知指令: {inner_cmd}')

                hb_task.cancel()

        except websockets.exceptions.ConnectionClosed as e:
            print(f'\n[{now()}] ❌ 连接断开: code={e.code}, reason={e.reason}')
        except ConnectionRefusedError:
            print(f'[{now()}] ❌ 连接被拒绝，服务端可能没启动')
        except Exception as e:
            print(f'\n[{now()}] ❌ 异常: {type(e).__name__}: {e}')

        # 断线重连
        retry_count += 1
        wait = min(5 * retry_count, 30)
        print(f'[{now()}] ⏳ {wait} 秒后重连 (第 {retry_count} 次重试)...')
        await asyncio.sleep(wait)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WebSocket 测试客户端（模拟一体机）')
    parser.add_argument('--url', default='ws://127.0.0.1:9000',
                        help='服务端地址，默认 ws://127.0.0.1:9000（本机测试用）')
    parser.add_argument('--device', required=True,
                        help='设备编号，如 TEST001')
    parser.add_argument('--name', default='测试设备',
                        help='设备名称')
    parser.add_argument('--auto-reply', action='store_true',
                        help='收到 addUser 后自动回执（默认手动不回）')
    parser.add_argument('--fail-rate', type=float, default=0.0,
                        help='模拟失败概率 0.0~1.0，默认 0.0')
    args = parser.parse_args()

    try:
        asyncio.run(main(args.url, args.device, args.name, args.auto_reply, args.fail_rate))
    except KeyboardInterrupt:
        print('\n\n再见！')
        sys.exit(0)
