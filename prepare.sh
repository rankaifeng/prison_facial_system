#!/bin/bash
#
# 在有网电脑上运行此脚本，自动准备所有部署文件
# 用法: chmod +x prepare.sh && ./prepare.sh
#
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR/deploy-package"

echo "============================================"
echo "  准备部署包..."
echo "============================================"
echo ""

# 清理旧的部署包
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# ── 1. 检查环境 ──
echo "[1/6] 检查环境..."

if ! command -v docker &>/dev/null; then
    echo "错误: 未安装 Docker"
    echo "Mac 请安装 Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "错误: Docker 未启动，请先打开 Docker Desktop 应用"
    exit 1
fi

if ! command -v node &>/dev/null; then
    echo "错误: 未安装 Node.js"
    exit 1
fi

echo "  Docker: $(docker --version)"
echo "  Node.js: $(node --version)"

# ── 2. 构建前端 ──
echo ""
echo "[2/6] 构建前端..."

cd "$SCRIPT_DIR"
npm install --silent
npm run build

if [ ! -d "$SCRIPT_DIR/dist" ]; then
    echo "错误: 前端构建失败，未生成 dist 目录"
    exit 1
fi
echo "  前端构建完成"

# ── 3. 构建 Docker 镜像 ──
echo ""
echo "[3/6] 构建 Docker 镜像（可能需要几分钟）..."

echo "  构建后端镜像 (linux/amd64)..."
if ! docker build --no-cache --platform linux/amd64 -f server/Dockerfile -t prison-backend:latest .; then
    echo "错误: 后端镜像构建失败"
    exit 1
fi

echo "  构建前端镜像 (linux/amd64)..."
if ! docker build --no-cache --platform linux/amd64 -f deployment/frontend/Dockerfile -t prison-frontend:latest .; then
    echo "错误: 前端镜像构建失败"
    exit 1
fi

echo "  镜像构建完成"

# ── 4. 导出镜像 ──
echo ""
echo "[4/6] 导出 Docker 镜像..."

docker save prison-backend:latest prison-frontend:latest -o "$DEPLOY_DIR/app-images.tar"

echo "  拉取基础镜像并导出 (linux/amd64)..."
docker pull mysql:8.0
docker pull redis:7-alpine

# 使用 --platform 只导出 amd64 架构的镜像
docker save --platform linux/amd64 mysql:8.0 redis:7-alpine -o "$DEPLOY_DIR/base-images.tar"

echo "  镜像导出完成"

# ── 5. 复制配置文件和脚本 ──
echo ""
echo "[5/6] 复制配置文件和脚本..."

cp "$SCRIPT_DIR/server/config/cameras.yml" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/proxy.py" "$DEPLOY_DIR/"

# 复制 install.sh 和 .env（模板文件在 deployment/ 目录下）
if [ -f "$SCRIPT_DIR/deployment/install.sh" ]; then
    cp "$SCRIPT_DIR/deployment/install.sh" "$DEPLOY_DIR/"
    cp "$SCRIPT_DIR/deployment/update.sh" "$DEPLOY_DIR/"
    cp "$SCRIPT_DIR/deployment/.env" "$DEPLOY_DIR/"
    chmod +x "$DEPLOY_DIR/install.sh" "$DEPLOY_DIR/update.sh"
else
    echo "错误: 未找到 deployment/install.sh 模板文件"
    exit 1
fi

echo "  完成"

# ── 6. 生成 Docker 离线安装脚本 ──
echo ""
echo "[6/6] 生成 Docker 离线安装说明..."

cat > "$DEPLOY_DIR/install-docker.sh" << 'DOCKEREOF'
#!/bin/bash
# 在 Ubuntu 服务器上安装 Docker（需要临时联网或提前安装）
# 如果服务器能临时联网：
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker
usermod -aG docker $USER
echo "Docker 安装完成: $(docker --version)"
DOCKEREOF
chmod +x "$DEPLOY_DIR/install-docker.sh"

echo "  完成"

# ── 输出结果 ──
echo ""
echo "============================================"
echo "  部署包准备完成！"
echo "============================================"
echo ""
echo "  部署包位置: $DEPLOY_DIR"
echo "  大小: $(du -sh "$DEPLOY_DIR" | cut -f1)"
echo ""
echo "  下一步:"
echo "  首次部署:"
echo "    1. 将 deploy-package 整个文件夹拷贝到服务器"
echo "    2. 修改 deploy-package/.env 中的 SERVER_IP"
echo "    3. 运行: sudo bash install.sh"
echo ""
echo "  更新部署（已部署过的服务器）:"
echo "    1. 将 deploy-package 拷贝到服务器"
echo "    2. 运行: sudo bash update.sh"
echo ""
