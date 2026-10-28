"""
大华门禁同步公共模块

逻辑与 test_dahua_face.py（已在设备上实测通过）保持一致：
  - is_ok: 响应以 "OK" 开头才算成功（设备失败返回 "Error\\nErrorID=..\\nErrorDescr=.."）
  - 人员: insertMulti 失败转 updateMulti
  - 人脸: 先 deleteMulti 清旧记录，再 insertMulti（不带 PhotoURL），失败转 updateMulti
  - 照片: RGB + 长边限 1280 + quality 90→10 逐档压缩，base64 后 <= 100KB
"""
import base64
from io import BytesIO

import requests
from PIL import Image

BASE64_LIMIT = 100 * 1024  # 接口限制: base64 后 <= 100KB
MAX_LONG_SIDE = 1280       # 先限制分辨率保画质，避免把 quality 压得过低
QUALITY_STEPS = (90, 80, 70, 60, 50, 40, 30, 20, 15, 10)


def is_ok(body):
    # 大华成功返回 "OK"，失败返回 "Error\nErrorID=..\nErrorDescr=.."
    return body.upper().startswith("OK")


def http_post_cgi(base_url, cgi_path, payload, auth, timeout=(5, 60)):
    """POST JSON 到设备 CGI，返回响应文本；401 时抛异常"""
    url = f"{base_url}/cgi-bin/{cgi_path}"
    r = requests.post(url, json=payload, timeout=timeout, auth=auth)
    body = r.text.strip()
    if r.status_code == 401:
        raise RuntimeError("认证失败(HTTP 401)，检查大华平台用户名/密码")
    return body


def fix_photo_url(url):
    """修正照片URL，兼容旧数据中的错误地址"""
    if not url:
        return url
    url = url.replace('http://10.2.48.86/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:80/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.48.86:8080/', 'http://10.2.50.16/')
    url = url.replace('http://10.2.50.16:8080/', 'http://10.2.50.16/')
    return url


def download_photo(photo_url, log=None):
    """下载照片，返回原始字节，失败返回 None"""
    if log is None:
        def log(msg):
            pass
    photo_url = fix_photo_url(photo_url)
    try:
        resp = requests.get(photo_url, timeout=15)
        resp.raise_for_status()
        content = resp.content
        if len(content) < 100:
            log(f'        照片文件过小({len(content)}B)，可能无效: {photo_url}')
            return None
        return content
    except requests.Timeout:
        log(f'        下载照片超时: {photo_url}')
        return None
    except requests.ConnectionError:
        log(f'        下载照片连接失败: {photo_url}')
        return None
    except requests.HTTPError as e:
        log(f'        下载照片HTTP错误({e.response.status_code}): {photo_url}')
        return None
    except Exception as e:
        log(f'        下载照片异常: {photo_url} -> {e}')
        return None


def prepare_photo(photo_bytes, log=None):
    """转 RGB + 限制分辨率 + JPEG 压缩，保证 base64 后不超限（与测试脚本一致）"""
    if log is None:
        def log(msg):
            pass
    img = Image.open(BytesIO(photo_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    long_side = max(img.size)
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / long_side
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        log(f'        缩放到: {img.size}')

    for quality in QUALITY_STEPS:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        raw = buf.getvalue()
        b64_len = (len(raw) + 2) // 3 * 4
        if b64_len <= BASE64_LIMIT:
            return raw
    raise RuntimeError(f"无法压到 {BASE64_LIMIT // 1024}KB 以内")


def build_user_payload(user_id, user_name, id_card=''):
    payload = {
        'UserID': user_id,
        'UserName': user_name,
        'UserType': 0,
        'UseTime': 1,
        'IsFirstEnter': True,
        'FirstEnterDoors': [0],
        'UserStatus': 0,
        'Authority': 2,
        'Password': '123456',
        'Doors': [0],
        'ValidFrom': '2026-01-01 00:00:00',
        'ValidTo': '2099-12-31 23:59:59',
    }
    if id_card:
        payload['CitizenIDNo'] = id_card
    return payload


def insert_user(base_url, auth, user_id, user_name, id_card='', log=None):
    """注册人员，已存在则转更新（与测试脚本 insert_user 一致）"""
    if log is None:
        def log(msg):
            pass
    payload = {'UserList': [build_user_payload(user_id, user_name, id_card)]}
    body = http_post_cgi(base_url, 'AccessUser.cgi?action=insertMulti', payload, auth)
    if is_ok(body):
        return True
    log(f'        插入失败: {body[:200]}，尝试转更新(updateMulti)...')
    body = http_post_cgi(base_url, 'AccessUser.cgi?action=updateMulti', payload, auth)
    if not is_ok(body):
        raise RuntimeError(f"人员注册/更新均失败: {body[:200]}")
    return True


def delete_face(base_url, auth, user_id, log=None):
    """清除该用户已有的人脸记录（没有记录时设备报错也无妨，继续）"""
    payload = {"FaceList": [{"UserID": user_id}]}
    try:
        http_post_cgi(base_url, 'AccessFace.cgi?action=deleteMulti', payload, auth, timeout=(5, 30))
    except Exception:
        pass


def insert_face(base_url, auth, user_id, photo_b64, log=None):
    """下发人脸照片（PhotoData 与 PhotoURL 二选一，只用 PhotoData；失败转 updateMulti）"""
    if log is None:
        def log(msg):
            pass
    payload = {"FaceList": [{"UserID": user_id, "PhotoData": [photo_b64]}]}
    body = http_post_cgi(base_url, 'AccessFace.cgi?action=insertMulti', payload, auth)
    if is_ok(body):
        return
    log(f'        insert 失败: {body[:200]}，尝试转 updateMulti...')
    body = http_post_cgi(base_url, 'AccessFace.cgi?action=updateMulti', payload, auth)
    if not is_ok(body):
        raise RuntimeError(f"人脸 insert/update 均失败: {body[:200]}")


def sync_users(base_url, auth, prisoners, log=None):
    """逐个同步人员信息。prisoners: [{'prisoner_no','prisoner_name','id_card'}, ...]
    返回 (success, fail)。单个失败不中断整体。"""
    if log is None:
        def log(msg):
            pass
    total = len(prisoners)
    success = 0
    fail = 0
    log(f'    开始同步用户，共 {total} 人...')
    for idx, p in enumerate(prisoners, 1):
        try:
            insert_user(base_url, auth, p['prisoner_no'], p['prisoner_name'], p.get('id_card', ''), log)
            success += 1
        except Exception as e:
            fail += 1
            log(f'        用户 {p["prisoner_no"]} 同步失败: {e}')
        if idx % 50 == 0:
            log(f'    用户进度: {idx}/{total} (成功 {success}, 失败 {fail})')
    log(f'    用户同步完成: 成功 {success}, 失败 {fail}')
    return success, fail


def sync_faces(base_url, auth, need_sync, log=None, on_success=None):
    """下载+压缩+下发人脸。need_sync: [(prisoner_no, photo_url), ...]
    on_success(prisoner_no, photo_url) 在单人下发成功后回调（用于更新 last_synced_photo_url）。
    返回 (success, fail, download_fail)。"""
    if log is None:
        def log(msg):
            pass
    total = len(need_sync)
    success = 0
    fail = 0
    download_fail = 0
    log(f'    开始同步人脸，共 {total} 人...')

    ready_count = 0
    for idx, (prisoner_no, photo_url) in enumerate(need_sync, 1):
        try:
            photo_bytes = download_photo(photo_url, log)
            if not photo_bytes:
                download_fail += 1
                continue
            raw_jpeg = prepare_photo(photo_bytes, log)
            photo_b64 = base64.b64encode(raw_jpeg).decode("ascii")
            delete_face(base_url, auth, prisoner_no, log)
            insert_face(base_url, auth, prisoner_no, photo_b64, log)
            success += 1
            ready_count += 1
            if on_success:
                try:
                    on_success(prisoner_no, photo_url)
                except Exception as e:
                    log(f'        更新同步标记失败 {prisoner_no}: {e}')
        except Exception as e:
            fail += 1
            log(f'        人脸下发失败 {prisoner_no}: {e}')
        if idx % 50 == 0:
            log(f'    人脸进度: {idx}/{total} (成功 {success}, 失败 {fail}, 下载失败 {download_fail})')

    log(f'    人脸同步完成: 成功 {success}, 失败 {fail}, 下载失败 {download_fail}')
    return success, fail, download_fail
