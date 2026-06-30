#!/bin/bash
#
# 准备部署包 - 智能构建，只在必要时重新构建镜像
# 用法: chmod +x prepare.sh && ./prepare.sh
#
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR/deploy-package"
CACHE_DIR="$SCRIPT_DIR/.build-cache"

# macOS 兼容的 md5 函数
file_md5() {
    if command -v md5sum &>/dev/null; then
        md5sum "$@" | cut -d' ' -f1
    else
        md5 -r "$@" | cut -d' ' -f1
    fi
}
pipe_md5() {
    if command -v md5sum &>/dev/null; then
        md5sum | cut -d' ' -f1
    else
        md5 -q
    fi
}

echo "============================================"
echo "  准备部署包..."
echo "============================================"
echo ""

# ── 1. 检查环境 ──
echo "[1/5] 检查环境..."

if ! command -v docker &>/dev/null; then
    echo "错误: 未安装 Docker"
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "错误: 未启动 Docker"
    exit 1
fi

if ! command -v node &>/dev/null; then
    echo "错误: 未安装 Node.js"
    exit 1
fi

echo "  Docker: $(docker --version | head -1)"
echo "  Node.js: $(node --version)"

# ── 2. 构建前端 ──
echo ""
echo "[2/5] 构建前端..."

cd "$SCRIPT_DIR"

# 检查前端是否需要重新构建
FRONTEND_HASH_FILE="$CACHE_DIR/frontend.hash"
CURRENT_FRONTEND_HASH=$(find src \( -name "*.jsx" -o -name "*.js" -o -name "*.css" \) | sort | while read f; do file_md5 "$f"; done | pipe_md5)
CACHED_FRONTEND_HASH=""

if [ -f "$FRONTEND_HASH_FILE" ]; then
    CACHED_FRONTEND_HASH=$(cat "$FRONTEND_HASH_FILE")
fi

if [ "$CURRENT_FRONTEND_HASH" = "$CACHED_FRONTEND_HASH" ] && [ -d "$SCRIPT_DIR/dist" ]; then
    echo "  前端代码未变化，跳过构建"
else
    echo "  正在构建前端..."
    npm install --silent 2>/dev/null
    npm run build
    mkdir -p "$CACHE_DIR"
    echo "$CURRENT_FRONTEND_HASH" > "$FRONTEND_HASH_FILE"
    echo "  前端构建完成"
fi

# ── 3. 检查后端镜像是否需要重建 ──
echo ""
echo "[3/5] 检查后端镜像..."

NEED_REBUILD=false

# 检查镜像是否存在
if ! docker image inspect prison-backend:latest &>/dev/null; then
    echo "  后端镜像不存在，需要构建"
    NEED_REBUILD=true
fi

# 检查 requirements.txt 是否变化
REQUIREMENTS_HASH_FILE="$CACHE_DIR/requirements.hash"
CURRENT_REQ_HASH=$(file_md5 "$SCRIPT_DIR/server/requirements.txt" 2>/dev/null)
CACHED_REQ_HASH=""

if [ -f "$REQUIREMENTS_HASH_FILE" ]; then
    CACHED_REQ_HASH=$(cat "$REQUIREMENTS_HASH_FILE")
fi

if [ "$CURRENT_REQ_HASH" != "$CACHED_REQ_HASH" ]; then
    echo "  requirements.txt 变化，需要重新构建"
    NEED_REBUILD=true
fi

# 检查 Dockerfile 是否变化
DOCKERFILE_HASH_FILE="$CACHE_DIR/dockerfile.hash"
CURRENT_DOCKER_HASH=$(file_md5 "$SCRIPT_DIR/server/Dockerfile" 2>/dev/null)
CACHED_DOCKER_HASH=""

if [ -f "$DOCKERFILE_HASH_FILE" ]; then
    CACHED_DOCKER_HASH=$(cat "$DOCKERFILE_HASH_FILE")
fi

if [ "$CURRENT_DOCKER_HASH" != "$CACHED_DOCKER_HASH" ]; then
    echo "  Dockerfile 变化，需要重新构建"
    NEED_REBUILD=true
fi

# 检查后端代码是否变化（.py, .sh, .yml, .html, .json 等）
BACKEND_CODE_HASH_FILE="$CACHE_DIR/backend-code.hash"
CURRENT_BACKEND_HASH=$(find server \( -name "*.py" -o -name "*.sh" -o -name "*.yml" -o -name "*.html" -o -name "*.json" -o -name "*.txt" \) | sort | while read f; do file_md5 "$f"; done | pipe_md5)
CACHED_BACKEND_HASH=""

if [ -f "$BACKEND_CODE_HASH_FILE" ]; then
    CACHED_BACKEND_HASH=$(cat "$BACKEND_CODE_HASH_FILE")
fi

if [ "$CURRENT_BACKEND_HASH" != "$CACHED_BACKEND_HASH" ]; then
    echo "  后端代码变化，需要重新构建"
    NEED_REBUILD=true
fi

# 构建或跳过
if [ "$NEED_REBUILD" = true ]; then
    echo "  正在构建后端镜像 (linux/amd64)..."
    echo "  首次构建约5-10分钟，后续有缓存会快很多..."
    if ! docker build --platform linux/amd64 -f server/Dockerfile -t prison-backend:latest .; then
        echo "错误: 后端镜像构建失败"
        exit 1
    fi
    mkdir -p "$CACHE_DIR"
    echo "$CURRENT_REQ_HASH" > "$REQUIREMENTS_HASH_FILE"
    echo "$CURRENT_DOCKER_HASH" > "$DOCKERFILE_HASH_FILE"
    echo "$CURRENT_BACKEND_HASH" > "$BACKEND_CODE_HASH_FILE"
    echo "  后端镜像构建完成"
else
    echo "  后端镜像无需重建，使用缓存"
fi

# 检查前端镜像
FRONTEND_DOCKER_HASH_FILE="$CACHE_DIR/frontend-dockerfile.hash"
CURRENT_FRONTEND_DOCKER_HASH=$(file_md5 "$SCRIPT_DIR/deployment/frontend/Dockerfile" 2>/dev/null)
CACHED_FRONTEND_DOCKER_HASH=""

if [ -f "$FRONTEND_DOCKER_HASH_FILE" ]; then
    CACHED_FRONTEND_DOCKER_HASH=$(cat "$FRONTEND_DOCKER_HASH_FILE")
fi

# 检查 dist/ 目录是否变化（前端构建产物）
FRONTEND_DIST_HASH_FILE="$CACHE_DIR/frontend-dist.hash"
CURRENT_DIST_HASH=$(find "$SCRIPT_DIR/dist" -type f | sort | while read f; do file_md5 "$f"; done | pipe_md5)
CACHED_DIST_HASH=""

if [ -f "$FRONTEND_DIST_HASH_FILE" ]; then
    CACHED_DIST_HASH=$(cat "$FRONTEND_DIST_HASH_FILE")
fi

NEED_FRONTEND_REBUILD=false
if ! docker image inspect prison-frontend:latest &>/dev/null; then
    NEED_FRONTEND_REBUILD=true
elif [ "$CURRENT_FRONTEND_DOCKER_HASH" != "$CACHED_FRONTEND_DOCKER_HASH" ]; then
    echo "  前端 Dockerfile 变化，需要重建"
    NEED_FRONTEND_REBUILD=true
elif [ "$CURRENT_DIST_HASH" != "$CACHED_DIST_HASH" ]; then
    echo "  前端构建产物变化，需要重建"
    NEED_FRONTEND_REBUILD=true
fi

if [ "$NEED_FRONTEND_REBUILD" = true ]; then
    echo "  正在构建前端镜像..."
    if ! docker build --platform linux/amd64 -f deployment/frontend/Dockerfile -t prison-frontend:latest .; then
        echo "错误: 前端镜像构建失败"
        exit 1
    fi
    mkdir -p "$CACHE_DIR"
    echo "$CURRENT_FRONTEND_DOCKER_HASH" > "$FRONTEND_DOCKER_HASH_FILE"
    echo "$CURRENT_DIST_HASH" > "$FRONTEND_DIST_HASH_FILE"
    echo "  前端镜像构建完成"
else
    echo "  前端镜像无需重建，使用缓存"
fi

# ── 4. 导出镜像 ──
echo ""
echo "[4/5] 导出 Docker 镜像..."

mkdir -p "$DEPLOY_DIR"

# 检查是否需要重新导出
APP_IMAGES_HASH_FILE="$CACHE_DIR/app-images.hash"
CURRENT_APP_HASH=$(docker inspect prison-backend:latest --format='{{.Id}}' 2>/dev/null)
CURRENT_APP_HASH="$CURRENT_APP_HASH$(docker inspect prison-frontend:latest --format='{{.Id}}' 2>/dev/null)"
CACHED_APP_HASH=""

if [ -f "$APP_IMAGES_HASH_FILE" ]; then
    CACHED_APP_HASH=$(cat "$APP_IMAGES_HASH_FILE")
fi

if [ "$CURRENT_APP_HASH" != "$CACHED_APP_HASH" ] || [ ! -f "$DEPLOY_DIR/app-images.tar" ]; then
    echo "  导出应用镜像..."
    docker save prison-backend:latest prison-frontend:latest -o "$DEPLOY_DIR/app-images.tar"
    echo "$CURRENT_APP_HASH" > "$APP_IMAGES_HASH_FILE"
    echo "  应用镜像导出完成: $(du -sh "$DEPLOY_DIR/app-images.tar" | cut -f1)"
else
    echo "  应用镜像未变化，跳过导出"
fi

# 基础镜像（只在不存在时拉取和导出）
if [ ! -f "$DEPLOY_DIR/base-images.tar" ]; then
    echo "  导出基础镜像 (mysql + redis)..."
    docker pull --quiet mysql:8.0 2>/dev/null || true
    docker pull --quiet redis:7-alpine 2>/dev/null || true
    docker save mysql:8.0 redis:7-alpine -o "$DEPLOY_DIR/base-images.tar"
    echo "  基础镜像导出完成: $(du -sh "$DEPLOY_DIR/base-images.tar" | cut -f1)"
else
    echo "  基础镜像已存在，跳过"
fi

# ── 5. 复制文件 ──
echo ""
echo "[5/5] 复制配置文件..."

# 配置文件
cp "$SCRIPT_DIR/server/config/cameras.yml" "$DEPLOY_DIR/"

# 部署脚本
cp "$SCRIPT_DIR/deployment/install.sh" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/update.sh" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/.env" "$DEPLOY_DIR/"
chmod +x "$DEPLOY_DIR/install.sh" "$DEPLOY_DIR/update.sh"

# nginx 配置
cp "$SCRIPT_DIR/deployment/frontend/nginx.conf" "$DEPLOY_DIR/"

# 读取 .env 中的 FRONTEND_PORT，更新 nginx.conf 端口
if [ -f "$SCRIPT_DIR/deployment/.env" ]; then
    FRONTEND_PORT=$(grep -E '^FRONTEND_PORT=' "$SCRIPT_DIR/deployment/.env" | cut -d'=' -f2 | tr -d '[:space:]')
fi
FRONTEND_PORT=${FRONTEND_PORT:-80}
if [ "$FRONTEND_PORT" != "80" ] && [ -f "$DEPLOY_DIR/nginx.conf" ]; then
    # macOS 和 Linux 都兼容的 sed -i
    sed -i.bak "s/listen       80/listen       $FRONTEND_PORT/" "$DEPLOY_DIR/nginx.conf"
    rm -f "$DEPLOY_DIR/nginx.conf.bak"
    echo "  nginx 端口已改为 $FRONTEND_PORT"
fi

echo "  完成"

# ── 输出结果 ──
echo ""
echo "============================================"
echo "  部署包准备完成！"
echo "============================================"
echo ""
echo "  位置: $DEPLOY_DIR"
echo "  大小: $(du -sh "$DEPLOY_DIR" | cut -f1)"
echo ""
echo "  下一步:"
echo "    1. 将 deploy-package 文件夹拷贝到服务器"
echo "    2. 修改 .env 中的 SERVER_IP"
echo "    3. 首次部署: sudo bash install.sh"
echo "    4. 更新部署: sudo bash update.sh"
echo ""
