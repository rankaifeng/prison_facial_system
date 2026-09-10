"""
大华人脸插入API测试
按文档4.12.2.3.1格式测试
独立运行: pip install requests pyyaml pillow && python3 test_face_api.py
"""
import requests
import yaml
import os
import json
import base64
from io import BytesIO

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'cameras.yml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

dahua = config.get('dahua', {})
base_url = dahua.get('base_url', '').rstrip('/')
username = dahua.get('userName', '')
password = dahua.get('password', '')
auth = requests.auth.HTTPDigestAuth(username, password)

print(f'设备: {base_url} (DH-ASI7213H)\n')

url = f"{base_url}/cgi-bin/AccessFace.cgi?action=insertMulti"

# ===== 准备测试图片 =====
# 生成一张模拟人脸的测试图(200x200 JPEG, <100KB)
from PIL import Image
img = Image.new('RGB', (200, 200), color=(180, 140, 120))  # 接近肤色
buf = BytesIO()
img.save(buf, format='JPEG', quality=50)
photo_bytes = buf.getvalue()
photo_b64 = base64.b64encode(photo_bytes).decode('utf-8')
# 注意：不加 data:image/jpeg;base64, 前缀，按文档要求直接用纯base64
print(f'测试图片: {len(photo_bytes)} bytes, base64: {len(photo_b64)} bytes')
print()

# ===== 准备测试用户 =====
print('[准备] 插入测试用户...')
for uid, name in [('DIAG_001', '测试1'), ('DIAG_002', '测试2')]:
    r = requests.post(f"{base_url}/cgi-bin/AccessUser.cgi?action=insertMulti",
                      json={'UserList': [{'UserID': uid, 'UserName': name, 'UserType': 0, 'UseTime': 1,
                                          'IsFirstEnter': True, 'FirstEnterDoors': [0], 'UserStatus': 0,
                                          'Authority': 2, 'CitizenIDNo': '', 'Password': '123456',
                                          'Doors': [0], 'ValidFrom': '2026-01-01 00:00:00',
                                          'ValidTo': '2099-12-31 23:59:59'}]},
                      auth=auth, timeout=10)
    print(f'  用户 {uid}: {r.status_code} {r.text.strip()}')
print()

# ===== 测试 =====

# 测试1: 单人 - 按文档格式 PhotoData数组
print('测试1: 单人 PhotoData=["base64"] (文档格式)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': [photo_b64], 'PhotoURL': []}
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试2: 单人 - PhotoData字符串(不包装数组)
print('测试2: 单人 PhotoData="base64" (字符串)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': photo_b64, 'PhotoURL': ''}
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试3: 批量2人 - 按文档格式
print('测试3: 批量2人 PhotoData=["base64"] (文档格式)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': [photo_b64], 'PhotoURL': []},
    {'UserID': 'DIAG_002', 'PhotoData': [photo_b64], 'PhotoURL': []},
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试4: 批量2人 - PhotoData字符串
print('测试4: 批量2人 PhotoData="base64" (字符串)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': photo_b64, 'PhotoURL': ''},
    {'UserID': 'DIAG_002', 'PhotoData': photo_b64, 'PhotoURL': ''},
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试5: 单人 - 不含FaceData字段(按文档示例)
print('测试5: 单人 无FaceData字段 (按文档示例)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': [photo_b64], 'PhotoURL': []}
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试6: 单人 - 只传PhotoData和UserID
print('测试6: 单人 只传UserID+PhotoData(数组)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': [photo_b64]}
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# 测试7: 单人 - 只传UserID+PhotoData(字符串)
print('测试7: 单人 只传UserID+PhotoData(字符串)')
r = requests.post(url, json={'FaceList': [
    {'UserID': 'DIAG_001', 'PhotoData': photo_b64}
]}, auth=auth, timeout=30)
print(f'  → {r.status_code} {r.text.strip()}')
print()

# ===== 清理 =====
print('[清理] 删除测试用户...')
for uid in ['DIAG_001', 'DIAG_002']:
    requests.get(f"{base_url}/cgi-bin/AccessUser.cgi?action=remove&UserID={uid}", auth=auth, timeout=10)

print('\n总结:')
print('  文档说 PhotoData 是 array<string>，单次最多10张')
print('  如果数组格式全失败但字符串格式成功，说明设备固件与文档不一致')
print('  如果批量失败但单人成功，说明设备只支持逐个插入')
