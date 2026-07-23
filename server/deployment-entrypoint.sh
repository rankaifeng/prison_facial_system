#!/bin/bash
# 注意：不使用 set -e，避免迁移失败导致容器崩溃后无限重启

echo "=== 等待 MySQL 就绪 ==="
for i in $(seq 1 30); do
    if python -c "import pymysql; pymysql.connect(host='${DB_HOST:-mysql}', port=${DB_PORT:-3306}, user='${DB_USER:-root}', password='${DB_PASSWORD:-123456}')" 2>/dev/null; then
        echo "MySQL 已就绪"
        break
    fi
    echo "等待 MySQL... ($i/30)"
    sleep 2
done

# 容错迁移：遇到"字段/表/记录已存在"类错误时自动 --fake 跳过该迁移并继续后续
# 这样既能跳过部分应用的迁移，又不会因为个别迁移失败让整个容器崩溃
run_migrate() {
    local max_retries=20
    local retry=0
    while [ $retry -lt $max_retries ]; do
        echo "=== 运行数据库迁移 (尝试 $((retry+1))/$max_retries) ==="
        local output
        if output=$(python manage.py migrate --noinput 2>&1); then
            echo "$output"
            echo "=== 迁移完成 ==="
            return 0
        fi

        echo "$output"

        # 只在"已存在"类错误时才 fake；其他错误（DB 连不上、语法错误等）不 fake
        if ! echo "$output" | grep -qE "Duplicate column name|already exists|Duplicate entry"; then
            echo "!!! 迁移失败且非'已存在'类错误，放弃自动修复"
            return 1
        fi

        # 从 Django 输出里提取失败的迁移项，格式：Applying users.0014_xxx...
        local failed
        failed=$(echo "$output" | grep -oE 'Applying [a-z_]+\.[0-9a-z_]+' | tail -1 | awk '{print $2}')
        if [ -z "$failed" ]; then
            echo "!!! 无法定位失败的迁移项，放弃自动修复"
            return 1
        fi

        local app migration
        app=$(echo "$failed" | cut -d. -f1)
        migration=$(echo "$failed" | cut -d. -f2)
        echo "!!! 检测到 $app.$migration 已部分应用，--fake 跳过该迁移"
        if ! python manage.py migrate "$app" "$migration" --fake --noinput 2>&1; then
            echo "!!! --fake 也失败，放弃"
            return 1
        fi
        retry=$((retry+1))
    done
    echo "!!! 超过最大重试次数 $max_retries"
    return 1
}

# 迁移失败也不阻塞容器启动，方便人工进入容器排查
run_migrate || echo "!!! 警告：数据库迁移未完全成功，容器仍将启动以便人工排查"

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
    else:
        print(f'管理员角色正常: {u.username}')
" || true

echo "=== 同步罪犯档案数据 ==="
python manage.py sync_prisoner_data --real-api || echo "同步罪犯数据失败，跳过继续启动"

echo "=== 启动 Daphne 服务（ASGI） ==="
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
