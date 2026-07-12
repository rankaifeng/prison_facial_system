"""
同步人脸照片到大华门禁平台

用法:
  python manage.py sync_dahua_faces              # 同步用户信息 + 人脸照片
  python manage.py sync_dahua_faces --full       # 完整同步：清空 → 插入用户 → 插入人脸
"""
import base64
import logging
import os
import time
import requests
import yaml
from io import BytesIO

from django.conf import settings
from django.core.management.base import BaseCommand
from apps.users.models import PrisonerArchive

logger = logging.getLogger(__name__)


def flush_print(msg=''):
    print(msg, flush=True)


class Command(BaseCommand):
    help = '同步人脸照片到大华门禁平台'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full', action='store_true', default=False,
            help='完整同步：清空设备 → 插入用户 → 插入人脸（默认只同步人脸）',
        )

    def handle(self, *args, **options):
        flush_print('\n=== 同步人脸照片到大华门禁平台 ===\n')

        # 1. 加载配置
        config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            flush_print(f'[错误] 加载 cameras.yml 失败: {e}')
            return

        dahua = config.get('dahua', {})
        base_url = dahua.get('base_url', '')
        if not base_url:
            flush_print('[错误] 大华平台 base_url 未配置')
            return

        username = dahua.get('userName', '')
        password = dahua.get('password', '')
        auth = requests.auth.HTTPDigestAuth(username, password) if username else None
        flush_print(f'大华地址: {base_url}')

        # 2. 测试连接
        flush_print('[1] 测试大华平台连接...')
        try:
            resp = requests.get(f"{base_url}/cgi-bin/magicBox.cgi?action=getDeviceType", auth=auth, timeout=(5, 10))
            flush_print(f'    连接成功: {resp.text.strip()[:100]}')
        except Exception as e:
            flush_print(f'[错误] 连接失败: {e}')
            return

        # 3. 读取档案数据
        flush_print('[2] 读取档案数据...')
        prisoners = list(PrisonerArchive.objects.all().values('prisoner_no', 'prisoner_name', 'id_card', 'media_info', 'last_synced_photo_url'))
        if not prisoners:
            flush_print('[警告] 档案库无数据，跳过')
            return
        flush_print(f'    共 {len(prisoners)} 人')

        full_mode = options['full']

        # 4. 完整模式：先清空旧数据
        if full_mode:
            flush_print('[3] 清空大华设备旧数据...')
            try:
                resp = requests.get(f"{base_url}/cgi-bin/AccessUser.cgi?action=removeAll", auth=auth, timeout=(5, 30))
                text = resp.text.strip().lower()
                if 'ok' in text:
                    flush_print('    清空成功')
                else:
                    flush_print(f'    清空返回: {resp.text[:200]}')
            except Exception as e:
                flush_print(f'    清空异常: {e}')

        # 5. 同步用户（必须先下发用户，才能下发人脸）
        flush_print('[4] 同步用户信息...')
        self._insert_users(base_url, auth, prisoners)

        # 6. 同步人脸
        flush_print(f'\n=== 开始同步人脸照片 ===\n')
        self._insert_faces(base_url, auth, prisoners)

    def _insert_users(self, base_url, auth, prisoners):
        url = f"{base_url}/cgi-bin/AccessUser.cgi?action=insertMulti"
        users = []
        for p in prisoners:
            users.append({
                'UserID': p['prisoner_no'],
                'UserName': p['prisoner_name'],
                'UserType': 0,
                'UseTime': 1,
                'IsFirstEnter': True,
                'FirstEnterDoors': [0],
                'UserStatus': 0,
                'Authority': 2,
                'CitizenIDNo': p.get('id_card', ''),
                'Password': '123456',
                'Doors': [0],
                'ValidFrom': '2026-01-01 00:00:00',
                'ValidTo': '2099-12-31 23:59:59',
            })

        batch_size = 10
        success = 0
        fail = 0
        total_batches = (len(users) + batch_size - 1) // batch_size
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            batch_num = i // batch_size + 1
            try:
                resp = requests.post(url, json={'UserList': batch}, auth=auth, timeout=(5, 30))
                text = resp.text.strip().lower()
                if 'ok' in text:
                    success += len(batch)
                    flush_print(f'    用户批次 {batch_num}/{total_batches}: 成功 {len(batch)} 个 (累计 {success}/{len(users)})')
                else:
                    fail += len(batch)
                    flush_print(f'    用户批次 {batch_num}/{total_batches} 失败: {resp.text[:200]}')
            except Exception as e:
                fail += len(batch)
                flush_print(f'    用户批次 {batch_num}/{total_batches} 异常: {e}')
            time.sleep(2)

        flush_print(f'    用户同步完成: 成功 {success}, 失败 {fail}')

    def _fix_photo_url(self, url):
        if not url:
            return url
        url = url.replace('http://10.2.48.86/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.48.86:80/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.48.86:8080/', 'http://10.2.50.16/')
        url = url.replace('http://10.2.50.16:8080/', 'http://10.2.50.16/')
        return url

    def _download_photo(self, photo_url):
        photo_url = self._fix_photo_url(photo_url)
        try:
            resp = requests.get(photo_url, timeout=15)
            resp.raise_for_status()
            content = resp.content
            if len(content) < 100:
                flush_print(f'        照片过小({len(content)}B): {photo_url}')
                return None
            return content
        except requests.Timeout:
            flush_print(f'        下载超时: {photo_url}')
            return None
        except requests.ConnectionError:
            flush_print(f'        连接失败: {photo_url}')
            return None
        except requests.HTTPError as e:
            flush_print(f'        HTTP错误({e.response.status_code}): {photo_url}')
            return None
        except Exception as e:
            flush_print(f'        下载异常: {photo_url} -> {e}')
            return None

    def _compress_photo(self, photo_bytes, max_size=50 * 1024):
        """压缩照片，目标50KB（base64后约67KB，留足够余量给请求头等开销）"""
        from PIL import Image
        img = Image.open(BytesIO(photo_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 先尝试不同质量
        for quality in (70, 55, 40, 30, 20, 15, 10):
            buf = BytesIO()
            img.save(buf, format='JPEG', quality=quality)
            if buf.tell() <= max_size:
                return buf.getvalue()

        # 质量压缩不够，缩小分辨率
        w, h = img.size
        for scale in (0.75, 0.5, 0.35, 0.25):
            resized = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            for quality in (50, 35, 20, 10):
                buf = BytesIO()
                resized.save(buf, format='JPEG', quality=quality)
                if buf.tell() <= max_size:
                    return buf.getvalue()

        return buf.getvalue()

    def _insert_faces(self, base_url, auth, prisoners):
        url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertMulti"

        # 增量比对：只同步照片URL有变化的
        no_photo = 0
        need_sync = []  # [(prisoner_no, photo_url), ...]
        for p in prisoners:
            media = p.get('media_info') or []
            current_url = ''
            for m in media:
                xp = self._fix_photo_url(m.get('xp', ''))
                if xp:
                    current_url = xp
                    break
            if not current_url:
                no_photo += 1
                continue
            if current_url != p.get('last_synced_photo_url', ''):
                need_sync.append((p['prisoner_no'], current_url))

        already_synced = len(prisoners) - no_photo - len(need_sync)
        flush_print(f'有照片: {len(prisoners) - no_photo} 人, 无照片: {no_photo} 人')
        flush_print(f'需同步: {len(need_sync)} 人, 已同步跳过: {already_synced} 人')

        if not need_sync:
            flush_print('所有照片已是最新，无需同步')
            return

        # 下载并压缩需要同步的照片
        flush_print('正在下载并压缩照片...')
        ready_list = []  # [(prisoner_no, photo_b64, photo_url), ...]
        download_fail = 0
        download_total = len(need_sync)
        download_count = 0
        for prisoner_no, photo_url in need_sync:
            download_count += 1
            photo_bytes = self._download_photo(photo_url)
            if not photo_bytes:
                download_fail += 1
                continue
            compressed = self._compress_photo(photo_bytes)
            photo_b64 = base64.b64encode(compressed).decode('utf-8')
            ready_list.append((prisoner_no, photo_b64, photo_url))
            if download_count % 50 == 0:
                flush_print(f'    下载进度: {download_count}/{download_total} (成功 {len(ready_list)}, 失败 {download_fail})')

        flush_print(f'准备就绪: {len(ready_list)} 人, 下载失败: {download_fail} 人')

        # 逐张验证大小，过滤掉仍然过大的
        final_list = []
        for prisoner_no, photo_b64, photo_url in ready_list:
            b64_size = len(photo_b64)
            if b64_size > 100 * 1024:  # base64超过100KB的跳过
                flush_print(f'        跳过 {prisoner_no}: 照片base64过大({b64_size // 1024}KB)')
                continue
            final_list.append((prisoner_no, photo_b64, photo_url))

        flush_print(f'验证通过: {len(final_list)} 人, 被过滤: {len(ready_list) - len(final_list)} 人')

        # 先测试单张照片，诊断问题
        flush_print('\n=== 诊断: 测试单张照片发送 ===')
        if final_list:
            test_pid, test_b64, test_url = final_list[0]
            flush_print(f'测试用户: {test_pid}, base64大小: {len(test_b64)} bytes')

            # 测试1: insertMulti 单张
            test_payload = {'FaceList': [{'UserID': test_pid, 'PhotoData': test_b64, 'PhotoURL': '', 'FaceData': ''}]}
            import json
            flush_print(f'insertMulti 请求体大小: {len(json.dumps(test_payload))} bytes')
            try:
                resp = requests.post(url, json=test_payload, auth=auth, timeout=(5, 30))
                flush_print(f'insertMulti 响应: [HTTP {resp.status_code}] {repr(resp.text)}')
                flush_print(f'insertMulti 响应头: {dict(resp.headers)}')
            except Exception as e:
                flush_print(f'insertMulti 异常: {e}')

            # 测试2: insertSingle
            single_url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertSingle"
            single_payload = {'UserID': test_pid, 'PhotoData': test_b64, 'PhotoURL': '', 'FaceData': ''}
            try:
                resp = requests.post(single_url, json=single_payload, auth=auth, timeout=(5, 30))
                flush_print(f'insertSingle 响应: [HTTP {resp.status_code}] {repr(resp.text)}')
            except Exception as e:
                flush_print(f'insertSingle 异常: {e}')

            # 测试3: 用 data= 发送原始JSON字符串，显式设置Content-Type
            try:
                raw_json = json.dumps(test_payload)
                resp = requests.post(url, data=raw_json,
                    headers={'Content-Type': 'application/json'},
                    auth=auth, timeout=(5, 30))
                flush_print(f'data+header 响应: [HTTP {resp.status_code}] {repr(resp.text)}')
            except Exception as e:
                flush_print(f'data+header 异常: {e}')

            # 测试4: 用 requests.Session 保持连接
            try:
                sess = requests.Session()
                sess.auth = auth
                resp = sess.post(url, json=test_payload, timeout=(5, 30))
                flush_print(f'Session.post 响应: [HTTP {resp.status_code}] {repr(resp.text)}')
            except Exception as e:
                flush_print(f'Session.post 异常: {e}')

        flush_print('=== 诊断结束 ===\n')

        # 根据诊断结果选择发送方式
        def _send_single(pid, b64_data):
            """发送单个人脸，返回 (ok, error_msg)"""
            single_payload = {'FaceList': [{'UserID': pid, 'PhotoData': b64_data, 'PhotoURL': '', 'FaceData': ''}]}
            try:
                r = requests.post(url, json=single_payload, auth=auth, timeout=(5, 60))
                if 'ok' in r.text.strip().lower():
                    return True, None
                return False, f'[HTTP {r.status_code}] {r.text.strip()}'
            except Exception as e:
                return False, str(e)

        # 批量发送，每批10张
        batch_size = 10
        success = 0
        fail = 0
        total_batches = (len(final_list) + batch_size - 1) // batch_size if final_list else 0
        flush_print(f'开始推送，共 {total_batches} 批...\n')

        for i in range(0, len(final_list), batch_size):
            batch = final_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            face_list = [{'UserID': pid, 'PhotoData': b64, 'PhotoURL': '', 'FaceData': ''} for pid, b64, _ in batch]
            payload = {'FaceList': face_list}
            payload_size = len(json.dumps(payload))
            batch_ok = False

            for attempt in range(3):
                try:
                    resp = requests.post(url, json=payload, auth=auth, timeout=(5, 120))
                    text = resp.text.strip().lower()
                    if 'ok' in text:
                        for prisoner_no, _, photo_url in batch:
                            PrisonerArchive.objects.filter(prisoner_no=prisoner_no).update(last_synced_photo_url=photo_url)
                        success += len(batch)
                        flush_print(f'    批次 {batch_num}/{total_batches}: 成功 {len(batch)} 个 (累计 {success}/{len(final_list)})')
                        batch_ok = True
                        break
                    else:
                        flush_print(f'    批次 {batch_num}/{total_batches} 尝试{attempt+1}/3 失败: [HTTP {resp.status_code}] {resp.text.strip()} (请求体 {payload_size // 1024}KB)')
                        if attempt < 2:
                            time.sleep(3)
                except Exception as e:
                    flush_print(f'    批次 {batch_num}/{total_batches} 尝试{attempt+1}/3 异常: {e}')
                    if attempt < 2:
                        time.sleep(3)

            if not batch_ok:
                flush_print(f'    批次 {batch_num}/{total_batches} 批量失败，逐个发送排查...')
                batch_success = 0
                batch_fail = 0
                for pid, b64_data, photo_url in batch:
                    ok, err = _send_single(pid, b64_data)
                    if ok:
                        PrisonerArchive.objects.filter(prisoner_no=pid).update(last_synced_photo_url=photo_url)
                        batch_success += 1
                    else:
                        batch_fail += 1
                        flush_print(f'        用户 {pid} 失败: {err} (base64 {len(b64_data) // 1024}KB)')
                    time.sleep(0.5)
                success += batch_success
                fail += batch_fail
                flush_print(f'    批次 {batch_num}/{total_batches} 逐个结果: 成功 {batch_success}, 失败 {batch_fail}')
            time.sleep(1)

        flush_print(f'\n人脸同步完成: 成功 {success}, 失败 {fail}, 无照片跳过 {no_photo}')
