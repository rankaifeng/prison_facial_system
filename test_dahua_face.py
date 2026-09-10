#!/usr/bin/env python3
"""
独立测试脚本：同步单张照片到大华门禁设备
不依赖项目任何代码，直接运行即可排查问题

用法: python3 test_dahua_face.py
"""

import base64
import json
import sys
from io import BytesIO

import requests
from requests.auth import HTTPDigestAuth
from PIL import Image

# ── 配置 ──
DEVICE_IP = "10.2.48.224"
PHOTO_URL = "http://10.2.50.16/202105/5106004250_11.jpg"
USER_ID = "5106004250"
MAX_PHOTO_SIZE = 100 * 1024  # 100KB
AUTH_USER = "admin"
AUTH_PASS = "sh123456"


def download_photo(url):
    """下载照片"""
    print(f"[1] 下载照片: {url}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        content = r.content
        print(f"    下载成功, 大小: {len(content)} bytes ({len(content)//1024}KB)")
        return content
    except Exception as e:
        print(f"    下载失败: {e}")
        return None


def compress_photo(photo_bytes, max_size=50 * 1024):
    """压缩照片到目标大小以下"""
    print(f"[2] 压缩照片 (目标: {max_size//1024}KB)")
    img = Image.open(BytesIO(photo_bytes))
    print(f"    原始尺寸: {img.size}, 模式: {img.mode}")
    if img.mode != 'RGB':
        img = img.convert('RGB')

    for quality in (70, 55, 40, 30, 20, 15, 10):
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        size = buf.tell()
        print(f"    quality={quality}: {size} bytes ({size//1024}KB)")
        if size <= max_size:
            print(f"    压缩完成, 最终大小: {size} bytes ({size//1024}KB)")
            return buf.getvalue()

    # 还是太大就缩放
    w, h = img.size
    for scale in (0.75, 0.5, 0.35, 0.25):
        resized = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        for quality in (50, 35, 20, 10):
            buf = BytesIO()
            resized.save(buf, format='JPEG', quality=quality)
            size = buf.tell()
            if size <= max_size:
                print(f"    缩放 {scale}x quality={quality}: {size} bytes ({size//1024}KB)")
                return buf.getvalue()

    print(f"    警告: 压缩后仍为 {buf.tell()} bytes")
    return buf.getvalue()


def encode_base64(photo_bytes):
    """转 base64（不含 data URI 前缀）"""
    b64 = base64.b64encode(photo_bytes).decode('utf-8')
    print(f"[3] Base64 编码: {len(b64)} bytes ({len(b64)//1024}KB)")
    # 检查是否超过 100KB
    if len(b64) > MAX_PHOTO_SIZE:
        print(f"    警告: base64 超过 100KB 限制!")
    return b64


def insert_user(device_ip, user_id):
    """先确保用户已注册"""
    url = f"http://{device_ip}/cgi-bin/AccessUser.cgi?action=insertMulti"
    payload = {
        "UserList": [{
            "UserID": user_id,
            "UserName": f"test_{user_id}",
            "UserType": 0,
            "UseTime": 1,
            "IsFirstEnter": True,
            "FirstEnterDoors": [0],
            "UserStatus": 0,
            "Authority": 2,
            "Password": "123456",
            "Doors": [0],
            "ValidFrom": "2026-01-01 00:00:00",
            "ValidTo": "2099-12-31 23:59:59",
        }]
    }
    print(f"[0] 注册用户: {user_id}")
    try:
        r = requests.post(url, json=payload, timeout=(5, 30), auth=HTTPDigestAuth(AUTH_USER, AUTH_PASS))
        print(f"    响应 [HTTP {r.status_code}]: {r.text.strip()}")
        return 'ok' in r.text.strip().lower()
    except Exception as e:
        print(f"    异常: {e}")
        return False


def insert_face(device_ip, user_id, photo_b64, photo_url):
    """下发人脸照片"""
    url = f"http://{device_ip}/cgi-bin/AccessFace.cgi?action=insertMulti"
    payload = {
        "FaceList": [{
            "UserID": user_id,
            "PhotoData":[photo_b64],
            "PhotoURL": [photo_url],
        }]
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    print(f"[4] 下发人脸到设备")
    print(f"    URL: {url}")
    print(f"    请求体总大小: {len(payload_json)} bytes ({len(payload_json)//1024}KB)")
    print(f"    完整JSON:")
    print(payload_json)
    print()
    try:
        r = requests.post(url, json=payload, timeout=(5, 60), auth=HTTPDigestAuth(AUTH_USER, AUTH_PASS))
        print(f"    响应 [HTTP {r.status_code}]: {r.text.strip()}")
        if 'ok' in r.text.strip().lower():
            print("    成功!")
            return True
        else:
            print("    失败!")
            return False
    except Exception as e:
        print(f"    异常: {e}")
        return False


def main():
    print("=" * 60)
    print("  大华门禁照片同步测试")
    print("=" * 60)
    print(f"  设备: {DEVICE_IP}")
    print(f"  用户: {USER_ID}")
    print(f"  照片: {PHOTO_URL}")
    print("=" * 60)
    print()

    # 1. 注册用户
    insert_user(DEVICE_IP, USER_ID)
    print()

    # 2. 下载照片
    photo_bytes = download_photo(PHOTO_URL)
    if not photo_bytes:
        print("照片下载失败，退出")
        sys.exit(1)
    print()

    # 3. 压缩照片
    compressed = compress_photo(photo_bytes)
    print()

    # 4. Base64 编码
    photo_b64 = encode_base64(compressed)
    print()

    # 5. 下发人脸
    insert_face(DEVICE_IP, USER_ID, photo_b64, PHOTO_URL)


if __name__ == '__main__':
    main()
