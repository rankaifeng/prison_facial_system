#!/usr/bin/env python3
"""
查询未来一年内即将刑满释放的人员名单（独立脚本，无需Django）

直接运行即可，脚本会自动探测数据库连接（兼容本地开发环境与服务器Docker环境），
无需手动修改任何配置。

用法:
    python3 query_upcoming_releases.py
    python3 query_upcoming_releases.py --area 一监区
    python3 query_upcoming_releases.py --csv
    python3 query_upcoming_releases.py --start 2026-09-20 --end 2027-09-20
    python3 query_upcoming_releases.py --host 10.2.48.100 --password xxx
"""

import os
import re
import csv
import sys
import argparse
from datetime import date
from pathlib import Path

try:
    import pymysql
except ImportError:
    print('缺少 pymysql，请先安装: pip3 install pymysql')
    sys.exit(1)

# ========== 默认数据库配置（来自 docker-compose.yml） ==========
DEFAULT_DB_HOST = '127.0.0.1'
DEFAULT_DB_PORT = 3306
DEFAULT_DB_USER = 'root'
DEFAULT_DB_NAME = 'prison_system'


def parse_env_file(path):
    """解析 .env 文件为 dict"""
    result = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                result[key.strip()] = val.strip()
    except (OSError, UnicodeDecodeError):
        pass
    return result


def build_db_candidates(args):
    """构建候选数据库配置列表（按优先级），供自动探测"""
    candidates = []
    seen = set()

    def add(host, port, user, password, database, source):
        if not host or not database:
            return
        key = (host, int(port), user, password, database)
        if key in seen:
            return
        seen.add(key)
        candidates.append({
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            '_source': source,
        })

    # 是否由命令行显式指定（显式指定则只尝试该配置）
    explicit = any([
        args.host != DEFAULT_DB_HOST,
        args.port != DEFAULT_DB_PORT,
        args.user != DEFAULT_DB_USER,
        args.password is not None,
        args.database != DEFAULT_DB_NAME,
    ])
    if explicit:
        add(args.host, args.port, args.user, args.password or '', args.database, '命令行参数')
        return candidates

    database = DEFAULT_DB_NAME
    user = DEFAULT_DB_USER

    # 1) 环境变量（Docker 容器内运行时）
    env_host = os.getenv('DB_HOST')
    if env_host:
        add(
            env_host,
            os.getenv('DB_PORT', '3306'),
            os.getenv('DB_USER', user),
            os.getenv('DB_PASSWORD', ''),
            os.getenv('DB_NAME', database),
            '环境变量',
        )

    # 2) 自动查找项目 .env（脚本即使不在项目中，也尝试几个常见位置）
    script_dir = Path(__file__).resolve().parent
    env_paths = [
        script_dir / '.env',
        script_dir / 'server' / '.env',
        Path.cwd() / '.env',
        Path.cwd() / 'server' / '.env',
    ]
    for env_path in env_paths:
        if env_path.exists():
            env = parse_env_file(env_path)
            add(
                env.get('DB_HOST', 'localhost'),
                env.get('DB_PORT', '3306'),
                env.get('DB_USER', user),
                env.get('DB_PASSWORD', ''),
                env.get('DB_NAME', database),
                f'.env ({env_path})',
            )

    # 3) 服务器 Docker 环境（端口映射后，带密码）
    add('127.0.0.1', 3306, 'root', 'Prison@2026', database, 'Docker默认')
    add('localhost', 3306, 'root', 'Prison@2026', database, 'Docker默认')

    # 4) 本地原生 MySQL（空密码）
    add('127.0.0.1', 3306, 'root', '', database, '本地空密码')
    add('localhost', 3306, 'root', '', database, '本地空密码')

    return candidates


def connect_with_fallback(candidates):
    """依次尝试候选配置，返回第一个成功的连接及其配置"""
    errors = []
    for cfg in candidates:
        try:
            conn = pymysql.connect(
                host=cfg['host'], port=cfg['port'], user=cfg['user'],
                password=cfg['password'], database=cfg['database'],
                charset=cfg.get('charset', 'utf8mb4'),
                connect_timeout=5,
            )
            return conn, cfg
        except pymysql.err.OperationalError as e:
            errors.append(f"  [{cfg['_source']}] {cfg['host']}:{cfg['port']} -> {e}")
        except Exception as e:
            errors.append(f"  [{cfg['_source']}] {cfg['host']}:{cfg['port']} -> {e}")
    return None, errors


def parse_sentence_end(raw):
    """解析刑期止日，支持多种日期格式"""
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    match = re.match(r'(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})', raw)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def query_records(conn, start_date, end_date, area=None, include_released=False):
    """从数据库查询并筛选（复用已建立的连接）"""
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        sql = 'SELECT prisoner_no, prisoner_name, gender, id_card, crime, sentence, sentence_start, sentence_end, prison_area, room_no, bed_no, is_released FROM prisoner_archive'
        conditions = []
        params = []
        if not include_released:
            conditions.append('is_released = %s')
            params.append(False)
        if area:
            conditions.append('prison_area LIKE %s')
            params.append(f'%{area}%')
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        sql += ' ORDER BY prisoner_no'
        cur.execute(sql, params)
        rows = cur.fetchall()

    today = date.today()
    results = []
    skipped = 0

    for row in rows:
        release_date = parse_sentence_end(row.get('sentence_end', ''))
        if release_date is None:
            skipped += 1
            continue
        if start_date <= release_date <= end_date:
            days_remaining = (release_date - today).days
            results.append({
                'prisoner_no': row.get('prisoner_no', ''),
                'prisoner_name': row.get('prisoner_name', ''),
                'gender': row.get('gender', ''),
                'id_card': row.get('id_card', ''),
                'crime': row.get('crime', ''),
                'sentence': row.get('sentence', ''),
                'sentence_start': row.get('sentence_start', ''),
                'sentence_end': row.get('sentence_end', ''),
                'prison_area': row.get('prison_area', ''),
                'room_no': row.get('room_no', ''),
                'bed_no': row.get('bed_no', ''),
                'status': '已释放' if row.get('is_released') else '在押',
                'days_remaining': days_remaining,
                'release_date': release_date,
            })

    results.sort(key=lambda x: x['release_date'])
    return results, skipped


def output_csv(results, start_str, end_str):
    """导出 CSV"""
    filename = f'即将释放人员_{start_str}_至_{end_str}.csv'
    fieldnames = [
        '序号', '罪犯编号', '姓名', '性别', '身份证号', '罪名',
        '原判刑期', '刑期起日', '刑期止日', '监区', '监室号', '床号',
        '在押状态', '剩余天数'
    ]
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(results, 1):
            writer.writerow({
                '序号': i,
                '罪犯编号': r['prisoner_no'],
                '姓名': r['prisoner_name'],
                '性别': r['gender'],
                '身份证号': r['id_card'],
                '罪名': r['crime'],
                '原判刑期': r['sentence'],
                '刑期起日': r['sentence_start'],
                '刑期止日': r['sentence_end'],
                '监区': r['prison_area'],
                '监室号': r['room_no'],
                '床号': r['bed_no'],
                '在押状态': r['status'],
                '剩余天数': r['days_remaining'],
            })
    print(f'已导出到文件: {filename}，共 {len(results)} 条')


def output_table(results, start_str, end_str, area, skipped):
    """终端表格输出"""
    print()
    print('=' * 100)
    msg = f'  刑满释放人员名单  |  {start_str} ~ {end_str}'
    if area:
        msg += f'  |  监区: {area}'
    print(msg)
    print('=' * 100)
    print()

    if not results:
        print('  未找到符合条件的人员')
        if skipped > 0:
            print()
            print(f'  注意: 有 {skipped} 条记录因刑期止日为空或格式无法识别而未参与筛选。')
            print('  如数量异常，请检查 prisoner_archive.sentence_end 字段的实际格式。')
        print()
        return

    header = f'{"序号":<4} {"编号":<12} {"姓名":<8} {"性别":<4} {"罪名":<18} {"原判刑期":<10} {"刑期止日":<12} {"监区":<10} {"监室":<6} {"剩余天数":<8} {"状态":<4}'
    print(header)
    print('-' * 100)

    for i, r in enumerate(results, 1):
        crime_display = r['crime'][:9] if len(r['crime']) > 9 else r['crime']
        line = (
            f'{i:<4} '
            f'{r["prisoner_no"]:<12} '
            f'{r["prisoner_name"]:<8} '
            f'{r["gender"]:<4} '
            f'{crime_display:<18} '
            f'{r["sentence"]:<10} '
            f'{r["sentence_end"]:<12} '
            f'{r["prison_area"]:<10} '
            f'{r["room_no"]:<6} '
            f'{r["days_remaining"]:<8} '
            f'{r["status"]:<4}'
        )
        if r['days_remaining'] <= 30:
            print(f'\033[93m{line}\033[0m')
        elif r['days_remaining'] <= 90:
            print(f'\033[96m{line}\033[0m')
        else:
            print(line)

    print('-' * 100)
    print()
    print(f'  合计: {len(results)} 人')
    if skipped > 0:
        print(f'  (跳过 {skipped} 条无有效刑期止日的记录)')
    print()

    # 按月统计
    monthly = {}
    for r in results:
        key = r['release_date'].strftime('%Y年%m月')
        monthly[key] = monthly.get(key, 0) + 1
    print('  按月统计:')
    for month, count in sorted(monthly.items()):
        bar = '█' * count
        print(f'    {month}: {count:>3} 人  {bar}')
    print()

    # 按监区统计
    area_stats = {}
    for r in results:
        a = r['prison_area'] or '未知'
        area_stats[a] = area_stats.get(a, 0) + 1
    print('  按监区统计:')
    for a, count in sorted(area_stats.items(), key=lambda x: x[1], reverse=True):
        bar = '█' * count
        print(f'    {a}: {count:>3} 人  {bar}')
    print()


def main():
    parser = argparse.ArgumentParser(description='查询即将刑满释放的人员名单')
    parser.add_argument('--start', type=str, default='2026-09-20', help='起始日期 (默认: 2026-09-20)')
    parser.add_argument('--end', type=str, default='2027-09-20', help='截止日期 (默认: 2027-09-20)')
    parser.add_argument('--area', type=str, default=None, help='按监区筛选')
    parser.add_argument('--csv', action='store_true', help='导出为 CSV 文件')
    parser.add_argument('--all', action='store_true', help='包含已释放人员')
    parser.add_argument('--host', type=str, default=DEFAULT_DB_HOST, help=f'数据库地址 (默认自动探测)')
    parser.add_argument('--port', type=int, default=DEFAULT_DB_PORT, help='数据库端口 (默认自动探测)')
    parser.add_argument('--user', type=str, default=DEFAULT_DB_USER, help='数据库用户 (默认自动探测)')
    parser.add_argument('--password', type=str, default=None, help='数据库密码 (默认自动探测)')
    parser.add_argument('--database', type=str, default=DEFAULT_DB_NAME, help='数据库名 (默认自动探测)')
    args = parser.parse_args()

    try:
        start_date = date.fromisoformat(args.start)
        end_date = date.fromisoformat(args.end)
    except ValueError:
        print(f'日期格式错误: {args.start} 或 {args.end}，请使用 YYYY-MM-DD')
        sys.exit(1)

    candidates = build_db_candidates(args)
    conn, result = connect_with_fallback(candidates)

    if conn is None:
        print('数据库连接失败，已尝试以下配置:')
        for err in result:
            print(err)
        print()
        print('请确认 MySQL 已启动，或通过 --host --port --user --password 手动指定连接信息')
        sys.exit(1)

    cfg = result
    print(f'数据库: {cfg["host"]}:{cfg["port"]}/{cfg["database"]} (来源: {cfg["_source"]})')
    print(f'正在查询 {args.start} ~ {args.end} 期间刑满释放人员...')
    try:
        results, skipped = query_records(conn, start_date, end_date, args.area, args.all)
    except Exception as e:
        print(f'查询失败: {e}')
        sys.exit(1)
    finally:
        conn.close()

    if args.csv:
        output_csv(results, args.start, args.end)
    else:
        output_table(results, args.start, args.end, args.area, skipped)


if __name__ == '__main__':
    main()
