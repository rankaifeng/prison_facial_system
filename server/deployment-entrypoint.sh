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

echo "=== 修复管理员角色 ==="
python -c "
from apps.users.models import User
for u in User.objects.filter(is_superuser=True):
    if u.role != 'admin':
        u.role = 'admin'
        u.role_name = '管理员'
        u.save()
        print(f'已修复管理员: {u.username}')
" || true

echo "=== 启动 Daphne 服务（ASGI） ==="
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
