#!/usr/bin/env python3
"""
独立脚本：同步档案库所有罪犯照片到大华门禁平台 (10.2.48.224)

用法：
  cd /Users/ran/Documents/work/prison_facial_system/server
  python ../test/sync_faces_to_dahua.py

  # 只同步指定罪犯
  python ../test/sync_faces_to_dahua.py --prisoner 5106004218

  # 只测试连接，不同步
  python ../test/sync_faces_to_dahua.py --test

  # 强制全量（忽略 last_synced_photo_url 增量标记）
  python ../test/sync_faces_to_dahua.py --full

接口文档（大华 AccessFace.cgi?action=insertMulti）：
  FaceList    array<object>   R  最大10条
  +UserID     string          R  用户ID
  +FaceData   array<string>   O  红光人脸模板Base64
  +PhotoData  array<string>   O  白光人脸照片Base64（纯base64，不含 data:image 前缀）
  +PhotoURL   array<string>   O  云端URL，和PhotoData二选一

关键：PhotoData 必须是**数组**，元素是纯 base64 字符串。
"""
import os
import sys
import base64
import json
import time
import argparse
import requests
import yaml
from datetime import datetime
from io import BytesIO

# ── Django 环境初始化（必须在 import models 之前）──
SERVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server')
sys.path.insert(0, os.path.abspath(SERVER_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.users.models import PrisonerArchive


# ── 配置 ──
def load_dahua_config():
    config_path = os.path.join(os.path.abspath(SERVER_DIR), 'config', 'cameras.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('dahua', {})


DAHUA = load_dahua_config()
BASE_URL = DAHUA.get('base_url', '').rstrip('/')
USERNAME = DAHUA.get('userName', '')
PASSWORD = DAHUA.get('password', '')
AUTH = requests.auth.HTTPDigestAuth(USERNAME, PASSWORD) if USERNAME else None


# ── 工具函数 ──
def now():
    return datetime.now().strftime('%H:%M:%S')


def log(msg):
    print(f'[{now()}] {msg}')


def fix_photo_url(url):
    """修正照片URL，兼容旧数据"""
    if not url:
        return url
    url = url.replace('http://10.2.48.86/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:80/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:8080/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.50.16:8080/', 'http://10.2.50.16/')
    return url


def select_photo_url(media_info):
    """从 media_info 取第一条 xp URL（与档案库列表逻辑一致）"""
    if not media_info:
        return ''
    for m in media_info:
        xp = m.get('xp', '')
        if xp:
            return fix_photo_url(xp)
    return ''


def download_photo(url, timeout=15):
    """下载照片，返回 bytes，失败返回 None"""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 100:
            return r.content
        log(f'    下载失败: HTTP {r.status_code}, {len(r.content)}B - {url}')
        return None
    except requests.Timeout:
        log(f'    下载超时: {url}')
        return None
    except Exception as e:
        log(f'    下载异常: {url} -> {e}')
        return None


def compress_photo(photo_bytes, max_size=80 * 1024):
    """压缩照片，目标 80KB（base64 后约 107KB，留余量）
    大华要求 PhotoData 单条 <= 100KB，所以 base64 后要 < 100KB
    """
    from PIL import Image
    img = Image.open(BytesIO(photo_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 先按质量压缩
    for quality in (80, 70, 60, 50, 40, 30):
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        if buf.tell() <= max_size:
            return buf.getvalue()

    # 不够再缩尺寸
    w, h = img.size
    for scale in (0.85, 0.75, 0.6, 0.5, 0.4):
        resized = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        for quality in (60, 45, 30, 20):
            buf = BytesIO()
            resized.save(buf, format='JPEG', quality=quality)
            if buf.tell() <= max_size:
                return buf.getvalue()
    return buf.getvalue()


def test_connection():
    """测试大华平台连通性"""
    url = f'{BASE_URL}/cgi-bin/magicBox.cgi?action=getDeviceType'
    try:
        r = requests.get(url, auth=AUTH, timeout=(5, 10))
        log(f'连接测试: HTTP {r.status_code}, 响应: {r.text.strip()[:100]}')
        return r.status_code == 200
    except Exception as e:
        log(f'连接失败: {e}')
        return False


def insert_user(prisoner):
    """插入单个用户（照片下发前必须先建用户）"""
    url = f'{BASE_URL}/cgi-bin/AccessUser.cgi?action=insertMulti'
    payload = {
        'UserList': [{
            'UserID': prisoner['prisoner_no'],
            'UserName': prisoner['prisoner_name'] or '未知',
            'UserType': 0,
            'UseTime': 1,
            'IsFirstEnter': True,
            'FirstEnterDoors': [0],
            'UserStatus': 0,
            'Authority': 2,
            'CitizenIDNo': prisoner.get('id_card', ''),
            'Password': '123456',
            'Doors': [0],
            'ValidFrom': '2026-01-01 00:00:00',
            'ValidTo': '2099-12-31 23:59:59',
        }]
    }
    try:
        r = requests.post(url, json=payload, auth=AUTH, timeout=(5, 30))
        return 'ok' in r.text.strip().lower()
    except Exception as e:
        log(f'    用户插入异常 {prisoner["prisoner_no"]}: {e}')
        return False


def insert_faces_batch(batch):
    """批量下发人脸（最多10条）
    batch: [(prisoner_no, photo_b64), ...]
    返回 (ok, resp_text)
    """
    url = f'{BASE_URL}/cgi-bin/AccessFace.cgi?action=insertMulti'
    # 关键：PhotoData 是数组，元素是纯 base64 字符串
    face_list = [
        {'UserID': pid, 'PhotoData': [b64], 'PhotoURL': []}
        for pid, b64 in batch
    ]
    payload = {'FaceList': face_list}
    try:
        r = requests.post(url, json=payload, auth=AUTH, timeout=(5, 120))
        text = r.text.strip()
        return 'ok' in text.lower(), text
    except Exception as e:
        return False, str(e)


def verify_face(prisoner_no):
    """查设备上某个用户是否有人脸照片"""
    url = f'{BASE_URL}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={prisoner_no}'
    try:
        r = requests.get(url, auth=AUTH, timeout=(5, 15))
        text = r.text
        if f'UserID={prisoner_no}' in text:
            idx = text.find(f'UserID={prisoner_no}')
            section = text[idx:idx + 500]
            return 'PhotoData=[' in section and 'PhotoData=[]' not in section
        return False
    except Exception:
        return False


# ── 主流程 ──
def sync(prisoner_filter=None, full=False):
    log('=' * 60)
    log('同步罪犯照片到大华门禁平台')
    log(f'设备地址: {BASE_URL}')
    log(f'账号: {USERNAME}')
    log('=' * 60)

    # 1. 测试连接
    log('[1/5] 测试大华平台连接...')
    if not test_connection():
        log('连接失败，退出')
        return
    log('    连接正常')

    # 2. 读取档案库
    log('[2/5] 读取档案库...')
    qs = PrisonerArchive.objects.all()
    if prisoner_filter:
        qs = qs.filter(prisoner_no=prisoner_filter)
    prisoners = list(qs.values('prisoner_no', 'prisoner_name', 'id_card', 'media_info', 'last_synced_photo_url'))
    log(f'    档案库共 {len(prisoners)} 人')

    if not prisoners:
        log('    无数据，退出')
        return

    # 3. 准备同步列表
    log('[3/5] 准备同步列表...')
    need_sync = []
    no_photo = 0
    already = 0
    for p in prisoners:
        photo_url = select_photo_url(p.get('media_info'))
        if not photo_url:
            no_photo += 1
            continue
        if not full and photo_url == p.get('last_synced_photo_url'):
            already += 1
            continue
        need_sync.append({
            'prisoner_no': p['prisoner_no'],
            'prisoner_name': p['prisoner_name'],
            'id_card': p.get('id_card', ''),
            'photo_url': photo_url,
        })

    log(f'    有照片: {len(prisoners) - no_photo} 人, 无照片: {no_photo} 人')
    log(f'    需同步: {len(need_sync)} 人, 已同步跳过: {already} 人')

    if not need_sync:
        log('    所有照片已是最新，无需同步')
        return

    # 4. 下载并压缩照片
    log('[4/5] 下载并压缩照片...')
    ready = []
    download_fail = 0
    for i, p in enumerate(need_sync, 1):
        photo_bytes = download_photo(p['photo_url'])
        if not photo_bytes:
            download_fail += 1
            continue
        compressed = compress_photo(photo_bytes)
        photo_b64 = base64.b64encode(compressed).decode('utf-8')
        if len(photo_b64) > 100 * 1024:
            log(f'    跳过 {p["prisoner_no"]}: base64 过大 {len(photo_b64) // 1024}KB')
            download_fail += 1
            continue
        ready.append((p, photo_b64))
        if i % 100 == 0:
            log(f'    进度: {i}/{len(need_sync)} (就绪 {len(ready)}, 失败 {download_fail})')

    log(f'    就绪: {len(ready)} 人, 下载失败: {download_fail} 人')

    if not ready:
        log('    无可同步照片，退出')
        return

    # 5. 先建用户，再下发照片
    log('[5/5] 同步用户和人脸到设备...')
    batch_size = 10
    total_batches = (len(ready) + batch_size - 1) // batch_size
    success = 0
    fail = 0

    for i in range(0, len(ready), batch_size):
        batch = ready[i:i + batch_size]
        batch_num = i // batch_size + 1

        # 5.1 先确保用户存在
        for p, _ in batch:
            insert_user(p)

        # 5.2 下发人脸照片
        face_batch = [(p['prisoner_no'], b64) for p, b64 in batch]
        ok, resp = insert_faces_batch(face_batch)

        if ok:
            # 更新 last_synced_photo_url
            for p, _ in batch:
                PrisonerArchive.objects.filter(
                    prisoner_no=p['prisoner_no']
                ).update(last_synced_photo_url=p['photo_url'])
            success += len(batch)
            log(f'    批次 {batch_num}/{total_batches}: 成功 {len(batch)} 个 (累计 {success}/{len(ready)})')
        else:
            fail += len(batch)
            log(f'    批次 {batch_num}/{total_batches} 失败: {resp[:200]}')
            # 失败时逐个重试，定位具体哪个错
            for p, b64 in batch:
                ok2, resp2 = insert_faces_batch([(p['prisoner_no'], b64)])
                if ok2:
                    PrisonerArchive.objects.filter(
                        prisoner_no=p['prisoner_no']
                    ).update(last_synced_photo_url=p['photo_url'])
                    success += 1
                    fail -= 1
                else:
                    log(f'        {p["prisoner_no"]} 失败: {resp2[:200]}')
                time.sleep(0.3)

        time.sleep(0.5)

    log('=' * 60)
    log(f'同步完成: 成功 {success}, 失败 {fail}, 下载失败 {download_fail}')
    log('=' * 60)

    # 6. 抽样验证
    if ready:
        log('[验证] 抽样查询设备上实际人脸...')
        sample = ready[:10]
        has_face = 0
        for p, _ in sample:
            if verify_face(p['prisoner_no']):
                has_face += 1
        log(f'[验证] 抽样 {len(sample)} 人: 有照片 {has_face}, 无照片 {len(sample) - has_face}')
        if has_face == 0:
            log('[验证] !!! 设备上查不到照片，可能照片质量不达标或设备拒绝')
        elif has_face < len(sample):
            log('[验证] 部分照片未存入设备')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='同步罪犯照片到大华门禁平台')
    parser.add_argument('--prisoner', help='只同步指定罪犯编号')
    parser.add_argument('--full', action='store_true', help='强制全量同步（忽略增量标记）')
    parser.add_argument('--test', action='store_true', help='只测试连接，不同步')
    args = parser.parse_args()

    if args.test:
        log('测试模式')
        test_connection()
    else:
        sync(prisoner_filter=args.prisoner, full=args.full)
