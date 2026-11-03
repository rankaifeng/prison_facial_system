#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监狱内网罪犯编号拉取脚本（独立运行，不依赖项目）

只拉在押罪犯编号列表，看接口到底返回多少人。

用法:
  python3 check_prisoner_sync.py
  python3 check_prisoner_sync.py --api 10.2.50.16:4092   # 指定 API 地址
  python3 check_prisoner_sync.py --out ids.json          # 编号保存到文件

仅依赖: pip3 install requests
"""
import argparse
import json
import re
import sys
from xml.etree import ElementTree as ET

try:
    import requests
except ImportError:
    print('缺少 requests 库，请先执行: pip3 install requests')
    sys.exit(1)

DEFAULT_API_BASE = 'http://10.2.50.16:4092'

GET_PRISONER_IDS_URL = "{base}/rti/service/invoke/arg0/unitop/arg1/unitop/arg2/zf_zyljbh/arg3/@zy='zy'"


def extract_inner_xml(soap_response):
    """从 SOAP 响应中提取 <return> 标签内容并还原 HTML 转义"""
    match = re.search(r'<return>(.*?)</return>', soap_response, re.DOTALL)
    if not match:
        return None
    text = match.group(1)
    return text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')


def fetch_prisoner_ids(base_url):
    """GET 获取所有在押罪犯编号"""
    url = GET_PRISONER_IDS_URL.format(base=base_url)
    print(f'请求编号列表: {url}')
    resp = requests.get(url, timeout=30)
    print(f'状态码: {resp.status_code}')
    resp.raise_for_status()

    print(f'响应内容(前500字符): {resp.text[:500]}')

    inner = extract_inner_xml(resp.text)
    if not inner:
        print(f'解析XML失败，原始响应前1000字符:\n{resp.text[:1000]}')
        return []

    print(f'解析到的内层XML(前500字符): {inner[:500]}')

    root = ET.fromstring(inner)
    ids = []
    for elem in root.findall('.//zyljbh'):
        x1 = elem.find('x1')
        if x1 is not None and x1.text:
            ids.append(x1.text.strip())

    # 去重：接口可能返回重复编号，不去重会虚报人数
    unique = list(dict.fromkeys(ids))
    dup = len(ids) - len(unique)
    if dup:
        print(f'    注意: 接口返回存在重复编号，重复 {dup} 个（已去重）')
    return unique


def main():
    parser = argparse.ArgumentParser(description='监狱内网罪犯编号拉取')
    parser.add_argument('--api', default=DEFAULT_API_BASE, help=f'API地址 (默认 {DEFAULT_API_BASE})')
    parser.add_argument('--out', default='', help='编号列表保存为JSON文件')
    args = parser.parse_args()

    base = args.api.rstrip('/')
    if not base.startswith('http'):
        base = 'http://' + base

    print('=' * 60)
    print('监狱内网罪犯编号拉取')
    print(f'API 地址: {base}')
    print('=' * 60)

    try:
        ids = fetch_prisoner_ids(base)
    except requests.RequestException as e:
        print(f'!! 拉取失败: {e}')
        sys.exit(1)

    print()
    print('*' * 60)
    print(f'*  接口返回在押罪犯总数: {len(ids)} 人')
    print('*' * 60)

    if ids:
        print()
        print('编号列表:')
        for pid in ids:
            print(f'    {pid}')

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump({'total': len(ids), 'ids': ids}, f, ensure_ascii=False, indent=2)
        print(f'\n编号已保存: {args.out}')


if __name__ == '__main__':
    main()
