"""
同步罪犯档案数据 - 部署时执行一次
从公安内网接口获取所有在押罪犯编号 → 查询基础信息 → 查询媒体信息 → 存入档案表

用法:
  python manage.py sync_prisoner_data              # 模拟数据（开发/测试）
  python manage.py sync_prisoner_data --real-api   # 真实接口（部署到公安内网后）
"""
import base64
import logging
import os
import re
import time
import requests
import yaml
from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import PrisonerArchive

logger = logging.getLogger(__name__)

# ========== 公安内网接口地址（从 .env 读取） ==========
API_BASE = os.getenv('RTI_API_BASE', 'http://10.2.50.16:4092')
GET_PRISONER_IDS_URL = f"{API_BASE}/rti/service/invoke/arg0/unitop/arg1/unitop/arg2/zf_zyljbh/arg3/@zy='zy'"
POST_SERVICE_URL = f'{API_BASE}/rti/service'

# ========== 模拟数据 ==========
MOCK_PRISONER_IDS = ['5106004218', '5155016879', '5155016428', '5106003856', '5155017201']

MOCK_BASIC_INFO = {
    '5155016428': {
        'bh': '5155016428', 'xm': '王志响', 'xb': '男', 'csrq': '1992.08.10', 'age': '33',
        'sfzh': '350583199208106015', 'mz': '汉族', 'bqwhcd': '初中', 'hy': '已婚',
        'jg': '福建省  南安市', 'jtmx': '福建省南安市东田镇桃园村罗城内22号',
        'zm': '非法经营', 'ypxq': '有期徒刑5年', 'zr': '2030.04.09', 'rjrq': '2026.02.06',
        'db': '一监区', 'jsh': '301', 'cwh': '5', 'zyxz': '在押',
        'dbjg': '四川省南充市高坪区公安局', 'pjjg': '四川省南充市高坪区人民法院',
        'pjzh': '(2025)川1303刑初第248号', 'zdah': '2602020', 'xq': '05_00_00',
        'syxq': '030930', 'jxcs': '0', 'fgdj': '考察级', 'nwfg': '无', 'sylb': '新收押',
        'drrq': '2026.02.06', 'yaflb': '一般刑事犯', 'xaflb': '一般刑事犯',
        'xscy': '新收', 'zyzt_cn': '在押', 'sfbm': '否', 'zbm': '王志响',
        'bqmm': '群众', 'jggj': '王耀辉', 'gz': '无', 'hkfl': '农村',
        'fzss': '2023年12月至2025年4月期间，该犯在未办理烟草专卖零售许可证、明知国内禁止销售水果味电子烟产品的情况下，从微信昵称"阿米尔汗"的上家处购买到大量水果味电子烟产品，通过网络发布售卖水果味电子烟产品的信息，使用其微信账号与买家联系、销售。经查证，该犯向多人销售水果味电子烟产品共计63,020.99元。',
    },
    '5106004218': {
        'bh': '5106004218', 'xm': '张三', 'xb': '男', 'csrq': '1988.05.12', 'age': '38',
        'sfzh': '510105198805120012', 'mz': '汉族', 'bqwhcd': '高中', 'hy': '已婚',
        'jg': '四川省  成都市', 'jtmx': '四川省成都市金牛区解放路123号',
        'zm': '盗窃罪', 'ypxq': '有期徒刑3年', 'zr': '2028.06.15', 'rjrq': '2025.06.15',
        'db': '一监区', 'jsh': '201', 'cwh': '3', 'zyxz': '在押',
        'dbjg': '四川省成都市金牛区公安局', 'pjjg': '四川省成都市金牛区人民法院',
        'pjzh': '(2025)川0106刑初第112号', 'zdah': '2501088', 'xq': '03_00_00',
        'syxq': '061500', 'jxcs': '0', 'fgdj': '考察级', 'nwfg': '无', 'sylb': '新收押',
        'drrq': '2025.06.15', 'yaflb': '一般刑事犯', 'xaflb': '一般刑事犯',
        'xscy': '新收', 'zyzt_cn': '在押', 'sfbm': '否', 'zbm': '张三',
        'bqmm': '群众', 'jggj': '李明', 'gz': '无', 'hkfl': '城市',
        'fzss': '该犯于2025年3月至5月期间，多次在成都市金牛区实施盗窃行为。',
    },
    '5155016879': {
        'bh': '5155016879', 'xm': '李四', 'xb': '男', 'csrq': '1995.03.20', 'age': '31',
        'sfzh': '511303199503200034', 'mz': '汉族', 'bqwhcd': '大专', 'hy': '未婚',
        'jg': '四川省  南充市', 'jtmx': '四川省南充市顺庆区人民北路45号',
        'zm': '故意伤害', 'ypxq': '有期徒刑4年', 'zr': '2029.08.20', 'rjrq': '2025.08.20',
        'db': '二监区', 'jsh': '305', 'cwh': '2', 'zyxz': '在押',
        'dbjg': '四川省南充市顺庆区公安局', 'pjjg': '四川省南充市顺庆区人民法院',
        'pjzh': '(2025)川1302刑初第89号', 'zdah': '2503012', 'xq': '04_00_00',
        'syxq': '082000', 'jxcs': '0', 'fgdj': '考察级', 'nwfg': '无', 'sylb': '新收押',
        'drrq': '2025.08.20', 'yaflb': '一般刑事犯', 'xaflb': '一般刑事犯',
        'xscy': '新收', 'zyzt_cn': '在押', 'sfbm': '否', 'zbm': '李四',
        'bqmm': '群众', 'jggj': '王强', 'gz': '无', 'hkfl': '城市',
        'fzss': '该犯于2025年6月因故意伤害罪被判处有期徒刑4年。',
    },
    '5106003856': {
        'bh': '5106003856', 'xm': '赵六', 'xb': '男', 'csrq': '1990.11.08', 'age': '35',
        'sfzh': '510722199011080056', 'mz': '汉族', 'bqwhcd': '初中', 'hy': '已婚',
        'jg': '四川省  绵阳市', 'jtmx': '四川省绵阳市涪城区长虹大道88号',
        'zm': '诈骗罪', 'ypxq': '有期徒刑6年', 'zr': '2031.01.10', 'rjrq': '2025.01.10',
        'db': '三监区', 'jsh': '402', 'cwh': '1', 'zyxz': '在押',
        'dbjg': '四川省绵阳市公安局', 'pjjg': '四川省绵阳市中级人民法院',
        'pjzh': '(2024)川07刑初第256号', 'zdah': '2409015', 'xq': '06_00_00',
        'syxq': '011000', 'jxcs': '0', 'fgdj': '考察级', 'nwfg': '无', 'sylb': '新收押',
        'drrq': '2025.01.10', 'yaflb': '一般刑事犯', 'xaflb': '一般刑事犯',
        'xscy': '新收', 'zyzt_cn': '在押', 'sfbm': '否', 'zbm': '赵六',
        'bqmm': '群众', 'jggj': '刘伟', 'gz': '无', 'hkfl': '城市',
        'fzss': '该犯于2023年至2024年期间，以投资理财为名实施诈骗行为。',
    },
    '5155017201': {
        'bh': '5155017201', 'xm': '孙七', 'xb': '男', 'csrq': '1997.07.25', 'age': '28',
        'sfzh': '511321199707250078', 'mz': '汉族', 'bqwhcd': '中专', 'hy': '未婚',
        'jg': '四川省  南充市', 'jtmx': '四川省南充市高坪区龙门街道12号',
        'zm': '抢劫罪', 'ypxq': '有期徒刑7年', 'zr': '2032.03.18', 'rjrq': '2025.03.18',
        'db': '二监区', 'jsh': '308', 'cwh': '4', 'zyxz': '在押',
        'dbjg': '四川省南充市高坪区公安局', 'pjjg': '四川省南充市高坪区人民法院',
        'pjzh': '(2025)川1303刑初第67号', 'zdah': '2503028', 'xq': '07_00_00',
        'syxq': '031800', 'jxcs': '0', 'fgdj': '考察级', 'nwfg': '无', 'sylb': '新收押',
        'drrq': '2025.03.18', 'yaflb': '暴力犯', 'xaflb': '暴力犯',
        'xscy': '新收', 'zyzt_cn': '在押', 'sfbm': '否', 'zbm': '孙七',
        'bqmm': '群众', 'jggj': '陈刚', 'gz': '无', 'hkfl': '农村',
        'fzss': '该犯于2025年1月伙同他人实施抢劫行为。',
    },
}

MOCK_MEDIA_DATA = {
    '5106004218': [
        {'bh': '5106004218', 'xm': '张三', 'mtbmm': '正面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5106004218_11.jpg', 'bmmc': '一监区', 'bz': ''},
    ],
    '5155016879': [
        {'bh': '5155016879', 'xm': '李四', 'mtbmm': '正面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5155016879_11.jpg', 'bmmc': '二监区', 'bz': ''},
        {'bh': '5155016879', 'xm': '李四', 'mtbmm': '侧面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5155016879_12.jpg', 'bmmc': '二监区', 'bz': '左侧'},
    ],
    '5155016428': [
        {'bh': '5155016428', 'xm': '王志响', 'mtbmm': '正面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5155016428_11.jpg', 'bmmc': '一监区', 'bz': ''},
    ],
    '5106003856': [
        {'bh': '5106003856', 'xm': '赵六', 'mtbmm': '正面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5106003856_11.jpg', 'bmmc': '三监区', 'bz': ''},
    ],
    '5155017201': [
        {'bh': '5155017201', 'xm': '孙七', 'mtbmm': '正面像', 'mtlb': '图像',
         'xp': r'C:\JGXTDB\zhao_pian\202602\5155017201_11.jpg', 'bmmc': '二监区', 'bz': ''},
    ],
}


def extract_inner_xml(soap_response):
    """从 SOAP 响应中提取内层 XML（<return> 标签中的内容），并还原 HTML 转义"""
    match = re.search(r'<return>(.*?)</return>', soap_response, re.DOTALL)
    if not match:
        return None
    text = match.group(1)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text


def cdata_text(element):
    """安全获取 XML 元素的文本内容（处理 CDATA）"""
    if element is None:
        return ''
    return (element.text or '').strip()


def build_soap_request(prisoner_id, service_code):
    """构造 SOAP POST 请求体"""
    return (
        "<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' "
        "xmlns:ser='http://service.rti/'>"
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<ser:invoke>"
        "<arg0>unitop</arg0>"
        "<arg1>unitop</arg1>"
        f"<arg2>{service_code}</arg2>"
        f"<arg3>@bh='{prisoner_id}'</arg3>"
        "</ser:invoke>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


class Command(BaseCommand):
    help = '同步公安内网罪犯档案数据（基本信息+媒体信息）到本地数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--real-api', action='store_true', default=False,
            help='调用真实公安内网接口（默认使用模拟数据）',
        )
        parser.add_argument(
            '--batch-size', type=int, default=50,
            help='每批处理数量，批间休息2秒（默认50）',
        )
        parser.add_argument(
            '--dahua', action='store_true', default=False,
            help='同步完成后推送到大华门禁平台',
        )

    def handle(self, *args, **options):
        use_real_api = options['real_api']
        batch_size = options['batch_size']
        mode = '真实接口' if use_real_api else '模拟数据'

        self.stdout.write(self.style.WARNING(f'=== 开始同步罪犯档案数据（模式: {mode}） ==='))

        # ── 第1步: 获取在押罪犯编号 ──
        self.stdout.write('\n>>> 第1步: 获取在押罪犯编号...')
        prisoner_ids = self._fetch_prisoner_ids(use_real_api)
        if not prisoner_ids:
            self.stdout.write(self.style.ERROR('未获取到任何罪犯编号，同步终止'))
            return
        self.stdout.write(self.style.SUCCESS(f'    获取到 {len(prisoner_ids)} 个编号'))

        # ── 第2步 + 第3步: 逐个查询基础信息和媒体信息，保存档案 ──
        self.stdout.write('\n>>> 第2步: 逐个查询基础信息 + 媒体信息并保存...')
        success = 0
        fail = 0

        for i, pid in enumerate(prisoner_ids, 1):
            try:
                basic = self._fetch_basic_info(pid, use_real_api)
                media = self._fetch_media_info(pid, use_real_api)
                self._save_archive(pid, basic, media)

                name = (basic or {}).get('xm', '未知') or '未知'
                media_count = len(media) if media else 0
                self.stdout.write(
                    f'    [{i}/{len(prisoner_ids)}] {pid} ({name}) '
                    f'- 基础信息: {"有" if basic else "无"}, 媒体: {media_count}条'
                )
                success += 1
            except Exception as e:
                fail += 1
                logger.error(f'处理罪犯 {pid} 失败: {e}')
                self.stdout.write(self.style.ERROR(f'    [{i}/{len(prisoner_ids)}] {pid} - 失败: {e}'))

            # 真实接口模式下，每批休息一下
            if use_real_api and i % batch_size == 0:
                self.stdout.write(f'    已处理 {i} 条，休息 2 秒...')
                time.sleep(2)

        # ── 汇总 ──
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'同步完成! 成功: {success}, 失败: {fail}'))
        self.stdout.write(self.style.SUCCESS(f'档案表 prisoner_archive 共 {PrisonerArchive.objects.count()} 条记录'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

        # ── 大华门禁平台同步 ──
        if options['dahua']:
            self._sync_to_dahua()

    # ==================== 接口调用 ====================

    def _fetch_prisoner_ids(self, use_real_api):
        """第1步: GET 获取所有在押罪犯编号"""
        if not use_real_api:
            self.stdout.write('    [模拟] 返回预设罪犯编号')
            return MOCK_PRISONER_IDS

        resp = requests.get(GET_PRISONER_IDS_URL, timeout=30)
        resp.raise_for_status()
        inner_xml = extract_inner_xml(resp.text)
        if not inner_xml:
            logger.error(f'解析罪犯编号XML失败: {resp.text[:500]}')
            return []

        root = ET.fromstring(inner_xml)
        ids = []
        for elem in root.findall('.//zyljbh'):
            x1 = elem.find('x1')
            if x1 is not None and x1.text:
                ids.append(x1.text.strip())
        return ids

    def _fetch_basic_info(self, prisoner_id, use_real_api):
        """第2步: POST 获取罪犯基础信息 (zf_jbxx_dg)"""
        if not use_real_api:
            return MOCK_BASIC_INFO.get(prisoner_id, {})

        soap_body = build_soap_request(prisoner_id, 'zf_jbxx_dg')
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        resp = requests.post(POST_SERVICE_URL, data=soap_body.encode('utf-8'),
                             headers=headers, timeout=30)
        resp.raise_for_status()
        inner_xml = extract_inner_xml(resp.text)
        if not inner_xml:
            return {}

        root = ET.fromstring(inner_xml)
        node = root.find('.//zf_jbxx_dg')
        if node is None:
            return {}

        # 将所有子元素解析为字典
        info = {}
        for child in node:
            tag = child.tag
            text = cdata_text(child)
            if tag in info:
                # 同名标签（如有）转列表
                if isinstance(info[tag], list):
                    info[tag].append(text)
                else:
                    info[tag] = [info[tag], text]
            else:
                info[tag] = text
        return info

    def _fetch_media_info(self, prisoner_id, use_real_api):
        """第3步: POST 获取媒体信息 (zf_mt_dg)"""
        if not use_real_api:
            return MOCK_MEDIA_DATA.get(prisoner_id, [])

        soap_body = build_soap_request(prisoner_id, 'zf_mt_dg')
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        resp = requests.post(POST_SERVICE_URL, data=soap_body.encode('utf-8'),
                             headers=headers, timeout=30)
        resp.raise_for_status()
        inner_xml = extract_inner_xml(resp.text)
        if not inner_xml:
            return []

        root = ET.fromstring(inner_xml)
        records = []
        for elem in root.findall('.//zf_mttz_dg'):
            records.append({
                'bh': cdata_text(elem.find('bh')),
                'xm': cdata_text(elem.find('xm')),
                'mtbmm': cdata_text(elem.find('mtbmm')),
                'mtlb': cdata_text(elem.find('mtlb')),
                'xp': cdata_text(elem.find('xp')),
                'bmmc': cdata_text(elem.find('bmmc')),
                'bz': cdata_text(elem.find('bz')),
            })
        return records

    # ==================== 数据保存 ====================

    @transaction.atomic
    def _save_archive(self, prisoner_no, basic_info, media_records):
        """保存或更新罪犯档案（编号唯一，存在则更新）"""
        basic_info = basic_info or {}
        media_records = media_records or []

        # 从基础信息中提取常用字段存入独立列
        def safe_int(val):
            try:
                return int(val) if val else None
            except (ValueError, TypeError):
                return None

        # 转换媒体信息中的相片路径
        def convert_photo_path(raw_path):
            """将 Windows 绝对路径转为 nginx 代理 URL"""
            if not raw_path:
                return ''
            # C:\JGXTDB\zhao_pian\202602\xxx.jpg → http://10.2.50.16/202602/xxx.jpg
            path = raw_path.replace('\\', '/')
            # 提取 zhao_pian 之后的部分
            marker = 'zhao_pian/'
            idx = path.find(marker)
            if idx >= 0:
                relative = path[idx + len(marker):]
            else:
                # 兜底：取最后两级目录
                parts = path.split('/')
                relative = '/'.join(parts[-2:]) if len(parts) >= 2 else parts[-1]
            # 去掉端口号，nginx 代理在 80 端口
            from urllib.parse import urlparse
            parsed = urlparse(API_BASE)
            base_url = f'{parsed.scheme}://{parsed.hostname}'
            relative = relative.lstrip('/')
            return f'{base_url}/{relative}'

        media_list = []
        seen_xp = set()
        for r in media_records:
            xp = convert_photo_path(r.get('xp', ''))
            if xp in seen_xp:
                continue
            seen_xp.add(xp)
            media_list.append({
                'bh': r.get('bh', ''),
                'xm': r.get('xm', ''),
                'mtbmm': r.get('mtbmm', ''),
                'mtlb': r.get('mtlb', ''),
                'xp': xp,
                'bmmc': r.get('bmmc', ''),
                'bz': r.get('bz', ''),
            })

        PrisonerArchive.objects.update_or_create(
            prisoner_no=prisoner_no,
            defaults={
                'prisoner_name': basic_info.get('xm', ''),
                'gender': basic_info.get('xb', ''),
                'birth_date': basic_info.get('csrq', ''),
                'age': safe_int(basic_info.get('age')),
                'id_card': basic_info.get('sfzh', ''),
                'nation': basic_info.get('mz', ''),
                'education': basic_info.get('bqwhcd', ''),
                'marital_status': basic_info.get('hy', ''),
                'native_place': basic_info.get('jg', ''),
                'address': basic_info.get('jtmx', ''),
                'crime': basic_info.get('zm', ''),
                'sentence': basic_info.get('ypxq', ''),
                'sentence_start': basic_info.get('zr', ''),
                'sentence_end': basic_info.get('syxq', ''),
                'prison_area': basic_info.get('db', ''),
                'room_no': basic_info.get('jsh', ''),
                'bed_no': basic_info.get('cwh', ''),
                'status': basic_info.get('zyxz', ''),
                'entry_date': basic_info.get('rjrq', ''),
                'arrest_org': basic_info.get('dbjg', ''),
                'judgment_org': basic_info.get('pjjg', ''),
                'judgment_no': basic_info.get('pjzh', ''),
                'basic_info': basic_info,
                'media_info': media_list,
            },
        )

    # ==================== 大华门禁平台同步 ====================

    def _load_dahua_config(self):
        """从 cameras.yml 加载大华配置"""
        config_path = os.path.join(settings.BASE_DIR, 'config', 'cameras.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('dahua', {})

    def _load_placeholder_face(self, dahua_config):
        """加载占位人脸图片并转为 base64（不含 data URI 前缀）"""
        face_path = os.path.join(settings.BASE_DIR, dahua_config.get('placeholder_face', 'imgs/face.jpeg'))
        if not os.path.exists(face_path):
            self.stdout.write(self.style.ERROR(f'占位人脸图片不存在: {face_path}'))
            return None
        with open(face_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _dahua_auth(self, base_url, auth):
        """验证大华平台连通性"""
        url = f"{base_url}/cgi-bin/magicBox.cgi?action=getDeviceType"
        try:
            resp = requests.get(url, auth=auth, timeout=10)
            text = resp.text.strip()
            self.stdout.write(self.style.SUCCESS(f'    大华平台连接成功: {resp}'))
            if text:
                self.stdout.write(self.style.SUCCESS(f'    大华平台连接成功: {text}'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    大华平台返回为空'))
                return False
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'    大华平台连接失败: {e}'))
            return False

    def _dahua_insert_users(self, base_url, auth, prisoners):
        """批量插入用户到大华门禁平台"""
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

        payload = {'UserList': users}
        try:
            resp = requests.post(url, json=payload, auth=auth, timeout=30)
            text = resp.text.strip().lower()
            if 'ok' in text:
                self.stdout.write(self.style.SUCCESS(f'    用户插入成功: {len(users)} 个'))
                return True
            else:
                self.stdout.write(self.style.ERROR(f'    用户插入失败: {resp.text[:200]}'))
                return False
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'    用户插入请求失败: {e}'))
            return False

    def _dahua_insert_faces(self, base_url, auth, prisoners, face_base64):
        """批量插入人脸照片到大华门禁平台"""
        url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertMulti"
        faces = []
        for p in prisoners:
            faces.append({
                'UserID': p['prisoner_no'],
                'FaceData': [],
                'PhotoData': [face_base64],
                'PhotoURL': [],
            })

        # 大华 API 可能有单次请求限制，分批处理
        batch_size = 50
        total_success = 0
        for i in range(0, len(faces), batch_size):
            batch = faces[i:i + batch_size]
            payload = {'FaceList': batch}
            try:
                resp = requests.post(url, json=payload, auth=auth, timeout=60)
                text = resp.text.strip().lower()
                if 'ok' in text:
                    total_success += len(batch)
                    self.stdout.write(f'    人脸批次 {i // batch_size + 1}: 插入 {len(batch)} 个')
                else:
                    self.stdout.write(self.style.ERROR(
                        f'    人脸批次 {i // batch_size + 1} 失败: {resp.text[:200]}'))
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'    人脸批次 {i // batch_size + 1} 请求失败: {e}'))

        if total_success > 0:
            self.stdout.write(self.style.SUCCESS(f'    人脸插入完成: {total_success}/{len(faces)}'))
        return total_success == len(faces)

    def _sync_to_dahua(self):
        """将档案库数据同步到大华门禁平台"""
        self.stdout.write('\n>>> 同步到大华门禁平台...')

        dahua_config = self._load_dahua_config()
        base_url = dahua_config.get('base_url', '')
        if not base_url:
            self.stdout.write(self.style.ERROR('    大华平台 base_url 未配置，请检查 config/cameras.yml'))
            return

        username = dahua_config.get('userName', '')
        password = dahua_config.get('password', '')
        auth = requests.auth.HTTPDigestAuth(username, password) if username else None

        # 1. 验证连通性
        if not self._dahua_auth(base_url, auth):
            return

        # 2. 加载占位人脸
        face_base64 = self._load_placeholder_face(dahua_config)
        if not face_base64:
            return

        # 3. 获取所有档案数据
        archives = PrisonerArchive.objects.all()
        prisoners = list(archives.values('prisoner_no', 'prisoner_name', 'id_card'))
        if not prisoners:
            self.stdout.write(self.style.WARNING('    档案库无数据，跳过大华同步'))
            return
        self.stdout.write(f'    待同步: {len(prisoners)} 人')

        # 4. 插入用户
        self._dahua_insert_users(base_url, auth, prisoners)

        # 5. 插入人脸
        self._dahua_insert_faces(base_url, auth, prisoners, face_base64)

        self.stdout.write(self.style.SUCCESS('    大华门禁平台同步完成'))
