#!/bin/bash
set -e

echo "=== 运行数据库迁移 ==="
python manage.py migrate --noinput

echo "=== 同步罪犯档案数据 ==="
python manage.py sync_prisoner_data --real-api || echo "同步罪犯数据失败，跳过继续启动"

echo "=== 启动 Django 服务 ==="
exec python manage.py runserver 0.0.0.0:8000
