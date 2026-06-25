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

    # 添加 PHOTO_BASE_URL（如果不存在）
    if ! grep -q "PHOTO_BASE_URL" "$INSTALL_DIR/docker-compose.yml"; then
        sed -i "/RTI_API_BASE/a\\      - PHOTO_BASE_URL=http://$SERVER_IP" "$INSTALL_DIR/docker-compose.yml"
        echo "  已添加 PHOTO_BASE_URL=http://$SERVER_IP"
    fi
fi

# ── 3. 更新图片代理服务 ──
echo ""
echo "[3/5] 更新图片代理..."

if [ -f "$SCRIPT_DIR/proxy.py" ]; then
    cp "$SCRIPT_DIR/proxy.py" "$INSTALL_DIR/proxy.py"

    cat > /etc/systemd/system/prison-proxy.service << SERVICEEOF
[Unit]
Description=Prison Photo Proxy
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/proxy.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

    systemctl daemon-reload
    systemctl enable prison-proxy 2>/dev/null
    systemctl restart prison-proxy
    echo "  图片代理服务已启动（端口 80）"
else
    echo "  未找到 proxy.py，跳过"
fi

# ── 4. 重启服务 ──
echo ""
echo "[4/5] 重启服务..."

cd "$INSTALL_DIR"
docker compose up -d --force-recreate backend celery-beat frontend 2>&1 | sed 's/^/    /'

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
