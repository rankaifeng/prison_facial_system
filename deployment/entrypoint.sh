#!/bin/bash
set -e

echo "=== 等待 MySQL 就绪 ==="
for i in $(seq 1 30); do
    if python -c "import pymysql; pymysql.connect(host='${DB_HOST:-mysql}', port=${DB_PORT:-3306}, user='${DB_USER:-root}', password='${DB_PASSWORD:-123456}')" 2>/dev/null; then
        echo "MySQL 已就绪"
        break
    fi
    echo "等待 MySQL... ($i/30)"
    sleep 2
done

echo "=== 运行数据库迁移 ==="
python manage.py migrate --noinput

echo "=== 修复字段类型 ==="
python -c "
from django.db import connection
c = connection.cursor()
try:
    c.execute('ALTER TABLE exit_entry_record MODIFY COLUMN exit_date DATETIME(6) NULL')
    c.execute('ALTER TABLE exit_entry_record MODIFY COLUMN entry_date DATETIME(6) NULL')
    print('字段类型已修复')
except Exception as e:
    print(f'字段修复跳过: {e}')
" || true

echo "=== 同步罪犯档案数据 ==="
python manage.py sync_prisoner_data --real-api || echo "同步罪犯数据失败，跳过继续启动"

echo "=== 启动 Daphne 服务（ASGI） ==="
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
