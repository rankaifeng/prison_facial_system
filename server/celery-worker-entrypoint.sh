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

echo "=== 启动视频队列 Worker（video，并发1，串行录制）==="
celery -A config worker -l info \
    -Q video --concurrency=1 \
    -n video@%h \
    --without-gossip --without-mingle --without-heartbeat &
VIDEO_PID=$!

echo "=== 启动默认队列 Worker（celery，并发2）==="
celery -A config worker -l info \
    -Q celery --concurrency=2 \
    -n default@%h \
    --without-gossip --without-mingle --without-heartbeat &
DEFAULT_PID=$!

trap 'kill "$VIDEO_PID" "$DEFAULT_PID" 2>/dev/null || true' TERM INT

wait
