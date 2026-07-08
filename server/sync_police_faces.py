#!/usr/bin/env python3
"""
同步民警/特警照片到大华智能事件设备 (10.2.48.223)

用法:
    python sync_police_faces.py /path/to/photos              # 同步新照片（自动跳过已存在）
    python sync_police_faces.py /path/to/photos --force      # 强制同步全部
    python sync_police_faces.py --clear                      # 清空设备上所有数据

照片命名规则: 张三.jpg（文件名去掉扩展名即为姓名）
支持递归扫描子文件夹，只处理最终的图片文件。
同一姓名不会重复插入，可安全重复运行。
照片超过100KB会自动压缩。
"""

import os
import sys
import base64
import hashlib
import io
import time
import requests

DAHUA_BASE_URL = "http://10.2.48.223"
USERNAME = "admin"
PASSWORD = "sh123456"
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
MAX_PHOTO_SIZE = 100 * 1024  # 100KB


def name_to_user_id(name):
    """用姓名生成固定的 UserID，避免重复"""
    h = hashlib.md5(name.encode('utf-8')).hexdigest()[:12]
    return f"police_{h}"


def collect_photos(folder):
    """递归收集所有图片文件，返回 [(姓名, 文件路径), ...]"""
    photos = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                name = os.path.splitext(f)[0]
                photos.append((name, os.path.join(root, f)))
    return photos


def compress_image(photo_path, max_size=MAX_PHOTO_SIZE):
    """压缩图片到指定大小以下，返回 base64 字符串"""
    from PIL import Image

    file_size = os.path.getsize(photo_path)
    if file_size <= max_size:
        # 不需要压缩，直接读取转 base64
        with open(photo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    # 需要压缩
    img = Image.open(photo_path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # 先尝试降低质量
    for quality in [85, 70, 55, 40, 30]:
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        if buf.tell() <= max_size:
            return base64.b64encode(buf.getvalue()).decode('utf-8')

    # 质量压缩不够，缩小分辨率
    for scale in [0.75, 0.5, 0.35, 0.25]:
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format='JPEG', quality=50)
        if buf.tell() <= max_size:
            return base64.b64encode(buf.getvalue()).decode('utf-8')

    # 最后兜底
    buf = io.BytesIO()
    img.resize((200, 200), Image.LANCZOS).save(buf, format='JPEG', quality=30)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def clear_all_users(auth):
    """清空设备上所有用户"""
    url = f"{DAHUA_BASE_URL}/cgi-bin/AccessUser.cgi?action=deleteAll"
    try:
        resp = requests.get(url, auth=auth, timeout=30)
        print(f"清空用户: {resp.text.strip()}")
    except Exception as e:
        print(f"清空失败: {e}")


def clear_all_faces(auth):
    """清空设备上所有人脸"""
    url = f"{DAHUA_BASE_URL}/cgi-bin/AccessFace.cgi?action=deleteAll"
    try:
        resp = requests.get(url, auth=auth, timeout=30)
        print(f"清空人脸: {resp.text.strip()}")
    except Exception as e:
        print(f"清空失败: {e}")


def get_existing_users_with_face(auth):
    """查询设备上已有用户及其人脸状态，返回 {UserID: has_face} 字典"""
    users = {}
    page = 1
    print("  查询用户列表...", end="", flush=True)
    while True:
        url = f"{DAHUA_BASE_URL}/cgi-bin/AccessUser.cgi?action=getMulti&UserCount=100&Page={page}"
        try:
            resp = requests.get(url, auth=auth, timeout=15)
            data = resp.json()
            user_list = data.get('UserList', [])
            if not user_list:
                break
            for u in user_list:
                uid = u.get('UserID', '')
                if uid:
                    users[uid] = False
            page += 1
        except Exception:
            break
    print(f" 共 {len(users)} 个用户")

    # 批量查询人脸信息（每批最多10个）
    uid_list = list(users.keys())
    total_batches = (len(uid_list) + 9) // 10
    has_face_count = 0

    for i in range(0, len(uid_list), 10):
        batch = uid_list[i:i + 10]
        batch_num = i // 10 + 1
        if batch_num % 20 == 0 or batch_num == total_batches:
            print(f"  查询人脸: {batch_num}/{total_batches} 批 (有照片: {has_face_count})", flush=True)

        params = '&'.join([f'UserIDList[{j}]={uid}' for j, uid in enumerate(batch)])
        url = f"{DAHUA_BASE_URL}/cgi-bin/AccessFace.cgi?action=list&{params}"
        try:
            resp = requests.get(url, auth=auth, timeout=15)
            text = resp.text
            for uid in batch:
                if f'UserID={uid}' in text:
                    idx = text.find(f'UserID={uid}')
                    section = text[idx:idx + 500]
                    if 'PhotoData=[' in section and 'PhotoData=[]' not in section:
                        users[uid] = True
                        has_face_count += 1
        except Exception:
            pass

    return users


def insert_user(auth, user_id, user_name):
    """插入单个用户"""
    url = f"{DAHUA_BASE_URL}/cgi-bin/AccessUser.cgi?action=insertMulti"
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
    resp = requests.post(url, json=payload, auth=auth, timeout=(5, 30))
    return resp


def insert_face(auth, user_id, photo_b64):
    """上传人脸照片（使用 insertMulti 接口）"""
    url = f"{DAHUA_BASE_URL}/cgi-bin/AccessFace.cgi?action=insertMulti"
    payload = {
        "FaceList": [{
            "UserID": user_id,
            "PhotoData": [photo_b64],
            "PhotoURL": [],
        }]
    }
    resp = requests.post(url, json=payload, auth=auth, timeout=(5, 60))
    return resp


def main():
    auth = requests.auth.HTTPDigestAuth(USERNAME, PASSWORD)

    # 测试连通性
    try:
        resp = requests.get(
            f"{DAHUA_BASE_URL}/cgi-bin/magicBox.cgi?action=getDeviceType",
            auth=auth, timeout=10
        )
        print(f"设备连接成功: {resp.status_code}")
    except Exception as e:
        print(f"设备连接失败: {e}")
        sys.exit(1)

    # 清空模式
    if len(sys.argv) >= 2 and sys.argv[1] == '--clear':
        print("正在清空设备数据...")
        clear_all_faces(auth)
        clear_all_users(auth)
        print("清空完成")
        return

    # 同步模式
    if len(sys.argv) < 2:
        print("用法:")
        print("  python sync_police_faces.py /path/to/photos         # 同步新照片（自动跳过已存在）")
        print("  python sync_police_faces.py /path/to/photos --force # 强制同步全部")
        print("  python sync_police_faces.py --clear                 # 清空设备数据")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"错误: {folder} 不是有效的文件夹")
        sys.exit(1)

    photos = collect_photos(folder)
    total = len(photos)
    print(f"共找到 {total} 张照片\n")

    # 用姓名生成固定 UserID，自动去重
    seen = set()
    photo_items = []
    for name, path in photos:
        if name in seen:
            continue
        seen.add(name)
        user_id = name_to_user_id(name)
        photo_items.append((user_id, name, path))

    if len(photo_items) < total:
        print(f"去重后: {len(photo_items)} 人 (去除 {total - len(photo_items)} 个重名)\n")

    total = len(photo_items)

    # 查询已有用户，跳过已有用户+人脸的（--force 跳过此步骤）
    if '--force' not in sys.argv:
        print("正在查询设备已有用户和人脸...")
        existing = get_existing_users_with_face(auth)
        has_face = sum(1 for v in existing.values() if v)
        no_face = sum(1 for v in existing.values() if not v)
        print(f"设备上已有 {len(existing)} 个用户 (有照片: {has_face}, 无照片: {no_face})\n")

        # 跳过已有用户+人脸的，只同步新的或没有照片的
        new_items = []
        for uid, name, path in photo_items:
            if uid in existing and existing[uid]:
                continue  # 已有用户且有照片，跳过
            new_items.append((uid, name, path))

        skipped = total - len(new_items)
        if skipped > 0:
            print(f"跳过已有照片: {skipped} 个，待同步: {len(new_items)} 个\n")
        photo_items = new_items
        total = len(photo_items)
    else:
        print("强制模式: 跳过已有用户检查\n")

    if total == 0:
        print("没有新数据需要同步")
        return

    print("=" * 40)
    print("开始同步（用户+人脸一起）")
    print("=" * 40)

    success = 0
    fail = 0
    failed_list = []

    for i, (user_id, name, path) in enumerate(photo_items, 1):
        size_kb = os.path.getsize(path) / 1024
        print(f"[{i}/{total}] {name} ({size_kb:.0f}KB) ... ", end="", flush=True)

        # 1. 插入用户
        try:
            resp = insert_user(auth, user_id, name)
            text = resp.text.strip()
            if 'ok' not in text.lower():
                print(f"用户插入失败: {text[:100]}")
                fail += 1
                continue
        except Exception as e:
            print(f"用户插入异常: {e}")
            fail += 1
            continue

        # 2. 压缩图片并上传人脸
        try:
            photo_b64 = compress_image(path)
            resp = insert_face(auth, user_id, photo_b64)
            text = resp.text.strip()
            if 'ok' in text.lower():
                print("成功")
                success += 1
            else:
                print(f"人脸失败: {text[:100]}")
                fail += 1
                failed_list.append(name)
        except Exception as e:
            print(f"人脸异常: {e}")
            fail += 1
            failed_list.append(name)

        if i % 50 == 0:
            print(f"--- 进度: {i}/{total} (成功 {success}, 失败 {fail}) ---")

        time.sleep(0.5)

    print(f"\n{'=' * 40}")
    print(f"完成: 成功 {success}, 失败 {fail}, 共 {total}")
    if failed_list:
        print(f"\n失败列表 ({len(failed_list)} 个):")
        for name in failed_list:
            print(f"  - {name}")
    print(f"{'=' * 40}")


if __name__ == '__main__':
    main()
