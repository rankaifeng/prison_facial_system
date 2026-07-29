#!/bin/bash
#
# 更新脚本 - 替换镜像、更新配置、重启服务
# 用法: sudo bash update.sh
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/prison_system"

echo ""
echo "============================================"
echo "   监狱管控平台 - 更新部署"
echo "============================================"
echo ""

# 检查是否已部署
if [ ! -f "$INSTALL_DIR/docker-compose.yml" ]; then
    echo "错误: 未找到 $INSTALL_DIR/docker-compose.yml"
    echo "请先运行 install.sh 进行首次部署"
    exit 1
fi

# 读取 .env 获取 SERVER_IP
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# ── 1. 导入新镜像 ──
echo "[1/6] 导入新镜像..."

if [ -f "$SCRIPT_DIR/app-images.tar" ]; then
    docker load -i "$SCRIPT_DIR/app-images.tar" 2>&1 | sed 's/^/    /'
    echo "  应用镜像导入完成"
else
    echo "  未找到 app-images.tar，跳过镜像更新"
fi

# ── 2. 更新 docker-compose.yml 环境变量 ──
echo ""
echo "[2/6] 更新配置..."

if [ -n "$SERVER_IP" ]; then
    # 确保 ALLOWED_HOSTS 包含当前 IP
    if ! grep -q "$SERVER_IP" "$INSTALL_DIR/docker-compose.yml"; then
        sed -i "s/ALLOWED_HOSTS=localhost,127.0.0.1,/ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP,/" "$INSTALL_DIR/docker-compose.yml"
        echo "  已添加 $SERVER_IP 到 ALLOWED_HOSTS"
    fi

    # 移除 PHOTO_BASE_URL（照片已改为相对路径，由 nginx 代理）
    if grep -q "PHOTO_BASE_URL" "$INSTALL_DIR/docker-compose.yml"; then
        sed -i '/PHOTO_BASE_URL/d' "$INSTALL_DIR/docker-compose.yml"
        echo "  已移除 PHOTO_BASE_URL（照片改用相对路径）"
    fi
fi

# 如果老部署的 docker-compose.yml 没有 celery-worker 服务，补上（从 celery-beat 段复用密码）
if ! grep -q "celery-worker:" "$INSTALL_DIR/docker-compose.yml"; then
    INSTALL_DIR_PY="$INSTALL_DIR" python3 <<'PYEOF'
import os, re
path = os.path.join(os.environ['INSTALL_DIR_PY'], 'docker-compose.yml')
content = open(path).read()
m = re.search(r'celery-beat:.*?DB_PASSWORD=(\S+)', content, re.DOTALL)
if not m:
    print('  警告: 无法从 celery-beat 段提取密码，跳过 celery-worker 补丁')
else:
    pwd = m.group(1)
    worker_block = f'''  celery-worker:
    image: prison-backend:latest
    container_name: prison-celery-worker
    command: ["/app/celery-worker-entrypoint.sh"]
    restart: always
    network_mode: host
    environment:
      - DEBUG=False
      - DB_HOST=127.0.0.1
      - DB_PORT=3306
      - DB_NAME=prison_system
      - DB_USER=root
      - DB_PASSWORD={pwd}
      - REDIS_URL=redis://127.0.0.1:6379/0
      - CELERY_BROKER_URL=redis://127.0.0.1:6379/0
      - CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started

'''
    if '  frontend:' in content:
        content = content.replace('  frontend:', worker_block + '  frontend:', 1)
        open(path, 'w').write(content)
        print('  已补上 celery-worker 服务到 docker-compose.yml')
    else:
        print('  警告: 找不到 frontend 定位点，跳过')
PYEOF
fi

# ── 3. 停止旧的图片代理服务（已由 nginx 处理）──
echo ""
echo "[3/6] 清理旧的图片代理..."

if systemctl is-active --quiet prison-proxy 2>/dev/null; then
    systemctl stop prison-proxy
    systemctl disable prison-proxy
    rm -f /etc/systemd/system/prison-proxy.service
    systemctl daemon-reload
    echo "  已停止旧的图片代理服务"
else
    echo "  图片代理服务未运行，跳过"
fi

# ── 4. 重启服务 ──
echo ""
echo "[4/6] 重启服务..."

cd "$INSTALL_DIR"

# 记录旧镜像 ID
OLD_BACKEND=$(docker images prison-backend:latest -q 2>/dev/null | head -1)
OLD_FRONTEND=$(docker images prison-frontend:latest -q 2>/dev/null | head -1)

# 停止并移除旧容器，确保用新镜像重建
docker compose stop backend celery-beat celery-worker frontend 2>&1 | sed 's/^/    /'
docker compose rm -f backend celery-beat celery-worker frontend 2>&1 | sed 's/^/    /'

# 启动新容器
docker compose up -d backend celery-beat celery-worker frontend 2>&1 | sed 's/^/    /'

# 检查镜像是否更新
NEW_BACKEND=$(docker images prison-backend:latest -q 2>/dev/null | head -1)
NEW_FRONTEND=$(docker images prison-frontend:latest -q 2>/dev/null | head -1)
if [ "$OLD_BACKEND" != "$NEW_BACKEND" ]; then
    echo "  后端镜像已更新"
else
    echo "  后端镜像未变化"
fi
if [ "$OLD_FRONTEND" != "$NEW_FRONTEND" ]; then
    echo "  前端镜像已更新"
else
    echo "  前端镜像未变化"
fi

echo ""
echo "  等待后端启动..."
sleep 10

echo "  服务状态:"
docker compose ps 2>/dev/null | sed 's/^/    /'

# ── 5. 数据库迁移 ──
echo ""
echo "[5/6] 数据库迁移..."

# 修复 exit_date/entry_date 字段类型（DateField -> DateTimeField）
# 如果已执行过则会跳过
docker exec prison-backend python manage.py migrate users 0012_exit_entry_datetime --fake 2>&1 | sed 's/^/    /' || true

# 确保数据库字段类型正确（幂等操作，已改过的不会报错）
docker exec prison-backend python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('ALTER TABLE exit_entry_record MODIFY COLUMN exit_date DATETIME(6) NULL'); c.execute('ALTER TABLE exit_entry_record MODIFY COLUMN entry_date DATETIME(6) NULL'); print('done')" 2>&1 | sed 's/^/    /' || true
echo "  数据库迁移完成"

# 补注册每日统计重置任务（老部署可能没注册过，幂等）
echo "  确保每日统计重置任务已注册..."
docker exec prison-backend python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
schedule, _ = CrontabSchedule.objects.get_or_create(
    minute='0', hour='0', day_of_week='*', day_of_month='*', month_of_year='*'
)
_, created = PeriodicTask.objects.get_or_create(
    name='每日统计重置',
    defaults={
        'crontab': schedule,
        'task': 'apps.users.tasks.reset_daily_stats',
        'args': json.dumps([]),
    }
)
print('created' if created else 'exists')
" 2>&1 | sed 's/^/    /'

# ── 6. 同步人脸照片到大华平台 ──
echo ""
echo "[6/6] 同步人脸照片到大华门禁平台..."
docker exec prison-backend python manage.py sync_dahua_faces 2>&1 | sed 's/^/    /' && echo "  大华同步完成" || echo "  大华同步失败，可稍后手动执行"

# ── 完成 ──
echo ""
echo "============================================"
echo "   更新完成！"
echo "============================================"
echo ""
