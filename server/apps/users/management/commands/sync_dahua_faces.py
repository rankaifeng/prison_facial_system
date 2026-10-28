"""
同步人脸照片到大华门禁平台

用法:
  python manage.py sync_dahua_faces              # 同步用户信息 + 人脸照片
  python manage.py sync_dahua_faces --full       # 完整同步：清空 → 插入用户 → 插入人脸

核心同步逻辑统一走 apps.users.services.dahua_sync（与 test_dahua_face.py 实测通过版本一致）
"""
import os

import requests
import yaml

from django.conf import settings
from django.core.management.base import BaseCommand
from apps.users.models import PrisonerArchive
from apps.users.services import dahua_sync


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
                if dahua_sync.is_ok(resp.text.strip()):
                    flush_print('    清空成功')
                else:
                    flush_print(f'    清空返回: {resp.text[:200]}')
            except Exception as e:
                flush_print(f'    清空异常: {e}')

        # 5. 同步用户（必须先下发用户，才能下发人脸）
        flush_print('[4] 同步用户信息...')
        dahua_sync.sync_users(base_url, auth, prisoners, log=flush_print)

        # 6. 收集需要同步人脸的 (编号, 照片URL)
        need_sync = []
        no_photo = 0
        for p in prisoners:
            media = p.get('media_info') or []
            current_url = ''
            for m in media:
                xp = dahua_sync.fix_photo_url(m.get('xp', ''))
                if xp:
                    current_url = xp
                    break
            if not current_url:
                no_photo += 1
                continue
            need_sync.append((p['prisoner_no'], current_url))

        flush_print(f'有照片: {len(need_sync)} 人, 无照片: {no_photo} 人')
        if not need_sync:
            flush_print('无可同步照片')
            return

        # 7. 逐人下发人脸（先清旧记录再下发，成功后更新 last_synced_photo_url）
        flush_print('\n=== 开始同步人脸照片 ===\n')
        dahua_sync.sync_faces(
            base_url, auth, need_sync, log=flush_print,
            on_success=lambda pid, url: PrisonerArchive.objects.filter(prisoner_no=pid).update(last_synced_photo_url=url),
        )
