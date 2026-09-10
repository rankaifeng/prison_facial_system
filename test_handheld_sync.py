"""
独立脚本：同步单条罪犯到手持终端
用法: python test_handheld_sync.py

步骤（与项目 handheld_sync_service.py 一致）:
  1. 注册人员: POST http://{ip}:{port}/api/v2/person/create
  2. 注册照片: POST http://{ip}:{port}/face/createByUrl
  3. 设置回调: POST http://{ip}:{port}/setIdentifyCallBack
"""
import json
import base64
import requests

# ============ 设备配置（来自 handheld_device.yml）============
DEVICE_IP = "10.10.55.25"
DEVICE_PORT = 8081
PASSWORD = "12345678"
CALLBACK_URL = "http://218.89.143.234:8080/api/v1/handheld-callback/"

# ============ 罪犯数据 ============
PRISONER_NO = "5155010916"
PRISONER_NAME = "吴桂创"  # 如果知道名字可以填
ID_CARD = "500343232323232323243"        # 如果知道身份证号可以填
PHOTO_URL = "http://10.2.50.16/202205/5155010916_11.jpg"

BASE_URL = f"http://{DEVICE_IP}:{DEVICE_PORT}"


def step1_register_person():
    """步骤1: 注册人员"""
    print(f"\n{'='*50}")
    print(f"步骤1: 注册人员")
    print(f"{'='*50}")

    persons = [{
        'id': PRISONER_NO,
        'name': PRISONER_NAME,
        'idcardNum': ID_CARD,
    }]

    url = f"{BASE_URL}/api/v2/person/create"
    data = {
        'pass': PASSWORD,
        'persons': json.dumps(persons, ensure_ascii=False),
    }

    print(f"请求: POST {url}")
    print(f"参数: pass={PASSWORD}, persons={json.dumps(persons, ensure_ascii=False)}")

    try:
        resp = requests.post(url, data=data, timeout=30)
        print(f"响应: HTTP {resp.status_code}")
        print(f"内容: {resp.text.strip()}")
        result = resp.json()
        if result.get('success'):
            print(">>> 注册人员成功")
        else:
            print(f">>> 注册人员失败: {result.get('msg', '')}")
        return result.get('success', False)
    except Exception as e:
        print(f">>> 请求异常: {e}")
        return False


def step2_register_photo():
    """步骤2: 注册照片（base64方式）"""
    print(f"\n{'='*50}")
    print(f"步骤2: 注册照片（base64方式）")
    print(f"{'='*50}")

    # 先下载照片转base64
    print(f"下载照片: {PHOTO_URL}")
    try:
        resp = requests.get(PHOTO_URL, timeout=15)
        resp.raise_for_status()
        img_base64 = base64.b64encode(resp.content).decode('utf-8')
        print(f"照片下载成功，大小: {len(resp.content)} bytes，base64长度: {len(img_base64)}")
    except Exception as e:
        print(f">>> 照片下载失败: {e}")
        return False

    url = f"{BASE_URL}/face/create"
    data = {
        'pass': PASSWORD,
        'personId': PRISONER_NO,
        'faceId': f'face_{PRISONER_NO}',
        'imgBase64': img_base64,
    }

    print(f"请求: POST {url}")
    print(f"参数: pass={PASSWORD}, personId={PRISONER_NO}, faceId=face_{PRISONER_NO}, imgBase64长度={len(img_base64)}")

    try:
        resp = requests.post(url, data=data, timeout=30)
        print(f"响应: HTTP {resp.status_code}")
        print(f"内容: {resp.text.strip()}")
        result = resp.json()
        if result.get('success'):
            print(">>> 注册照片成功")
        else:
            print(f">>> 注册照片失败: {result.get('msg', '')}")
        return result.get('success', False)
    except Exception as e:
        print(f">>> 请求异常: {e}")
        return False


def step3_set_callback():
    """步骤3: 设置识别回调"""
    print(f"\n{'='*50}")
    print(f"步骤3: 设置识别回调")
    print(f"{'='*50}")

    url = f"{BASE_URL}/setIdentifyCallBack"
    data = {
        'pass': PASSWORD,
        'callbackUrl': CALLBACK_URL,
    }

    print(f"请求: POST {url}")
    print(f"参数: pass={PASSWORD}, callbackUrl={CALLBACK_URL}")

    try:
        resp = requests.post(url, data=data, timeout=10)
        print(f"响应: HTTP {resp.status_code}")
        print(f"内容: {resp.text.strip()}")
        result = resp.json()
        if result.get('success'):
            print(">>> 设置回调成功")
        else:
            print(f">>> 设置回调失败: {result.get('msg', '')}")
        return result.get('success', False)
    except Exception as e:
        print(f">>> 请求异常: {e}")
        return False


if __name__ == '__main__':
    print(f"设备: {BASE_URL}")
    print(f"罪犯编号: {PRISONER_NO}")
    print(f"照片地址: {PHOTO_URL}")

    r1 = step1_register_person()
    r2 = step2_register_photo()
    r3 = step3_set_callback()

    print(f"\n{'='*50}")
    print(f"结果汇总: 人员{'成功' if r1 else '失败'}，照片{'成功' if r2 else '失败'}，回调{'成功' if r3 else '失败'}")
    print(f"{'='*50}")
