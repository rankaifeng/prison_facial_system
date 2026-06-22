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

echo "=== 启动 Celery Beat 定时任务 ==="
exec celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
