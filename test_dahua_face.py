#!/usr/bin/env python3
"""
独立测试脚本：同步人员信息 + 人脸照片到大华门禁设备

流程：
  1. AccessUser.cgi?action=insertMulti  注册人员（已存在则转 updateMulti）
  2. 获取照片（URL 下载或本地文件）
  3. 压缩到接口限制内（base64 后 <= 100KB）
  4. AccessFace.cgi?action=insertMulti  下发人脸照片（仅 PhotoData，不带 PhotoURL）

用法:
  python3 test_dahua_face.py                          # 用脚本内默认配置
  python3 test_dahua_face.py --user-id 102 --photo /path/to/face.jpg
  python3 test_dahua_face.py --photo https://xxx/face.jpg
"""

import argparse
import base64
import sys
from io import BytesIO

import requests
from requests.auth import HTTPDigestAuth
from PIL import Image

# ── 默认配置（命令行参数可覆盖）──
DEFAULT_DEVICE_IP = "10.2.48.224"
DEFAULT_USER_ID = "510600425022"
DEFAULT_USER_NAME = "测试人员"
DEFAULT_PHOTO = "https://c-ssl.dtstatic.com/uploads/blog/202309/08/8gSMABJACgXEdZM.thumb.1000_0.png"
AUTH_USER = "admin"
AUTH_PASS = "sh123456"

# 接口文档: 白光人脸照片 100k x 5（每张 100KB，最多 5 张）
# 按 base64 串长度 <= 100KB 卡口，对应原始 JPEG 约 74KB
BASE64_LIMIT = 100 * 1024
MAX_LONG_SIDE = 1280  # 先限制分辨率保画质，避免把 quality 压得过低


def http_post(device_ip, cgi_path, payload):
    url = f"http://{device_ip}/cgi-bin/{cgi_path}"
    r = requests.post(url, json=payload, timeout=(5, 60),
                      auth=HTTPDigestAuth(AUTH_USER, AUTH_PASS))
    body = r.text.strip()
    if r.status_code == 401:
        raise RuntimeError(f"认证失败(HTTP 401)，检查用户名/密码: {AUTH_USER}")
    return body


def is_ok(body):
    # 大华成功返回 "OK"，失败返回 "Error\nErrorID=..\nErrorDescr=.."
    return body.upper().startswith("OK")


def load_photo(photo_src):
    """URL 下载或读取本地文件"""
    if photo_src.startswith("http://") or photo_src.startswith("https://"):
        print(f"[1] 下载照片: {photo_src}")
        r = requests.get(photo_src, timeout=15)
        r.raise_for_status()
        data = r.content
    else:
        print(f"[1] 读取本地照片: {photo_src}")
        with open(photo_src, "rb") as f:
            data = f.read()
    print(f"    原始大小: {len(data)} bytes ({len(data)//1024}KB)")
    return data


def prepare_photo(photo_bytes):
    """转 RGB + 限制分辨率 + JPEG 压缩，保证 base64 后不超限"""
    print(f"[2] 压缩照片 (base64 后上限 {BASE64_LIMIT//1024}KB)")
    img = Image.open(BytesIO(photo_bytes))
    print(f"    原始尺寸: {img.size}, 模式: {img.mode}")
    if img.mode != "RGB":
        img = img.convert("RGB")

    long_side = max(img.size)
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / long_side
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        print(f"    缩放到: {img.size}")

    best = None
    for quality in (90, 80, 70, 60, 50, 40, 30, 20, 15, 10):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        raw = buf.getvalue()
        b64_len = (len(raw) + 2) // 3 * 4
        if b64_len <= BASE64_LIMIT:
            print(f"    quality={quality}: {len(raw)} bytes -> base64 {b64_len} bytes ✓")
            return raw
        best = (quality, len(raw))
        print(f"    quality={quality}: {len(raw)} bytes -> base64 {b64_len} bytes (超限)")

    q, size = best
    raise RuntimeError(f"无法压到 {BASE64_LIMIT//1024}KB 以内（最接近 quality={q}, {size} bytes）")


def insert_user(device_ip, user_id, user_name):
    """注册人员，已存在则转更新"""
    payload = {
        "UserList": [{
            "UserID": user_id,
            "UserName": user_name,
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
    print(f"[3] 注册人员: {user_id} ({user_name})")
    body = http_post(device_ip, "AccessUser.cgi?action=insertMulti", payload)
    if is_ok(body):
        print(f"    注册成功: {body}")
        return True

    print(f"    插入失败: {body}")
    print(f"    尝试转为更新(updateMulti)...")
    body = http_post(device_ip, "AccessUser.cgi?action=updateMulti", payload)
    print(f"    响应: {body}")
    if not is_ok(body):
        raise RuntimeError(f"人员注册/更新均失败: {body}")
    return True


def delete_face(device_ip, user_id):
    """清除该用户已有的人脸记录（没有记录时设备报错也无妨，继续）"""
    payload = {"FaceList": [{"UserID": user_id}]}
    print(f"[4a] 清除旧人脸记录 (如无记录可忽略报错)")
    body = http_post(device_ip, "AccessFace.cgi?action=deleteMulti", payload)
    print(f"    响应: {body.strip()}")


def insert_face(device_ip, user_id, photo_b64):
    """下发人脸照片（文档: PhotoData 与 PhotoURL 二选一，这里只用 PhotoData）"""
    payload = {
        "FaceList": [{
            "UserID": user_id,
            "PhotoData": [photo_b64],
        }]
    }
    print(f"[4b] 下发人脸照片")
    print(f"    base64 大小: {len(photo_b64)} bytes ({len(photo_b64)//1024}KB)")
    body = http_post(device_ip, "AccessFace.cgi?action=insertMulti", payload)
    print(f"    响应: {body}")
    if is_ok(body):
        print("    人脸下发成功!")
        return

    print("    insert 失败，尝试转 updateMulti...")
    body = http_post(device_ip, "AccessFace.cgi?action=updateMulti", payload)
    print(f"    响应: {body}")
    if not is_ok(body):
        raise RuntimeError(f"人脸 insert/update 均失败: {body}")
    print("    update 成功!")


def main():
    parser = argparse.ArgumentParser(description="同步人员+人脸到大华门禁设备")
    parser.add_argument("--ip", default=DEFAULT_DEVICE_IP, help=f"设备IP (默认 {DEFAULT_DEVICE_IP})")
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help=f"用户ID (默认 {DEFAULT_USER_ID})")
    parser.add_argument("--name", default=DEFAULT_USER_NAME, help=f"姓名 (默认 {DEFAULT_USER_NAME})")
    parser.add_argument("--photo", default=DEFAULT_PHOTO, help="照片路径或URL (默认脚本内配置)")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  设备: {args.ip}")
    print(f"  用户: {args.user_id} ({args.name})")
    print(f"  照片: {args.photo}")
    print("=" * 60 + "\n")

    try:
        photo_bytes = load_photo(args.photo)
        raw_jpeg = prepare_photo(photo_bytes)
        photo_b64 = base64.b64encode(raw_jpeg).decode("ascii")
        insert_user(args.ip, args.user_id, args.name)
        delete_face(args.ip, args.user_id)
        insert_face(args.ip, args.user_id, photo_b64)
    except Exception as e:
        print(f"\n✗ 失败: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✓ 全部完成")


if __name__ == "__main__":
    main()
