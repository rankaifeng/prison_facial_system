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
echo "[1/5] 导入新镜像..."

if [ -f "$SCRIPT_DIR/app-images.tar" ]; then
    docker load -i "$SCRIPT_DIR/app-images.tar" 2>&1 | sed 's/^/    /'
    echo "  应用镜像导入完成"
else
    echo "  未找到 app-images.tar，跳过镜像更新"
fi

# ── 2. 更新 docker-compose.yml 环境变量 ──
echo ""
echo "[2/5] 更新配置..."

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

# ── 3. 停止旧的图片代理服务（已由 nginx 处理）──
echo ""
echo "[3/5] 清理旧的图片代理..."

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
echo "[4/5] 重启服务..."

cd "$INSTALL_DIR"

# 记录旧镜像 ID
OLD_BACKEND=$(docker images prison-backend:latest -q 2>/dev/null | head -1)
OLD_FRONTEND=$(docker images prison-frontend:latest -q 2>/dev/null | head -1)

# 停止并移除旧容器，确保用新镜像重建
docker compose stop backend celery-beat frontend 2>&1 | sed 's/^/    /'
docker compose rm -f backend celery-beat frontend 2>&1 | sed 's/^/    /'

# 启动新容器
docker compose up -d backend celery-beat frontend 2>&1 | sed 's/^/    /'

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

# ── 5. 同步数据（修复图片路径等） ──
echo ""
echo "[5/5] 同步罪犯档案数据..."
docker exec prison-backend python manage.py sync_prisoner_data --real-api 2>&1 | sed 's/^/    /' && echo "  数据同步完成" || echo "  数据同步失败，可稍后手动执行"

# ── 完成 ──
echo ""
echo "============================================"
echo "   更新完成！"
echo "============================================"
echo ""
