#!/bin/bash
#
# 更新脚本 - 只替换镜像并重启服务
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

# ── 1. 导入新镜像 ──
echo "[1/3] 导入新镜像..."

if [ -f "$SCRIPT_DIR/app-images.tar" ]; then
    docker load -i "$SCRIPT_DIR/app-images.tar" 2>&1 | sed 's/^/    /'
    echo "  应用镜像导入完成"
else
    echo "错误: 未找到 app-images.tar"
    exit 1
fi

# ── 2. 重启服务 ──
echo ""
echo "[2/3] 重启服务..."

cd "$INSTALL_DIR"
docker compose up -d --force-recreate backend celery-beat frontend 2>&1 | sed 's/^/    /'

echo ""
echo "  等待后端启动..."
sleep 10

echo "  服务状态:"
docker compose ps 2>/dev/null | sed 's/^/    /'

# ── 3. 完成 ──
echo ""
echo "============================================"
echo "   更新完成！"
echo "============================================"
echo ""
