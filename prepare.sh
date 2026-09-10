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

# 计算目录内容的 hash（所有文件的 md5 汇总再取 hash）
dir_hash() {
    find "$1" -type f 2>/dev/null | sort | while read f; do file_md5 "$f"; done | pipe_md5
}

echo "============================================"
echo "  准备部署包..."
echo "============================================"
echo ""

mkdir -p "$CACHE_DIR"

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

FRONTEND_HASH_FILE="$CACHE_DIR/frontend.hash"
CURRENT_FRONTEND_HASH=$(find src \( -name "*.jsx" -o -name "*.js" -o -name "*.css" \) | sort | while read f; do file_md5 "$f"; done | pipe_md5)
CACHED_FRONTEND_HASH=$(cat "$FRONTEND_HASH_FILE" 2>/dev/null || echo "")

if [ "$CURRENT_FRONTEND_HASH" = "$CACHED_FRONTEND_HASH" ] && [ -d "$SCRIPT_DIR/dist" ]; then
    echo "  前端代码未变化，跳过构建"
else
    echo "  正在构建前端..."
    npm install --silent 2>/dev/null
    npm run build
    echo "$CURRENT_FRONTEND_HASH" > "$FRONTEND_HASH_FILE"
    echo "  前端构建完成"
fi

# ── 3. 构建后端镜像 ──
echo ""
echo "[3/5] 检查后端镜像..."

BACKEND_HASH_FILE="$CACHE_DIR/backend.hash"
# 后端 hash = requirements.txt + Dockerfile + 所有后端代码
CURRENT_BACKEND_HASH=$(
    { file_md5 "$SCRIPT_DIR/server/requirements.txt" 2>/dev/null;
      file_md5 "$SCRIPT_DIR/server/Dockerfile" 2>/dev/null;
      find server \( -name "*.py" -o -name "*.sh" -o -name "*.yml" -o -name "*.html" -o -name "*.json" \) | sort | while read f; do file_md5 "$f"; done; } | pipe_md5
)
CACHED_BACKEND_HASH=$(cat "$BACKEND_HASH_FILE" 2>/dev/null || echo "")

if docker image inspect prison-backend:latest &>/dev/null && [ "$CURRENT_BACKEND_HASH" = "$CACHED_BACKEND_HASH" ]; then
    echo "  后端镜像无需重建，使用缓存"
else
    echo "  正在构建后端镜像 (linux/amd64)..."
    echo "  首次构建约5-10分钟，后续有缓存会快很多..."
    if ! docker build --platform linux/amd64 -f server/Dockerfile -t prison-backend:latest .; then
        echo "错误: 后端镜像构建失败"
        exit 1
    fi
    echo "$CURRENT_BACKEND_HASH" > "$BACKEND_HASH_FILE"
    echo "  后端镜像构建完成"
fi

# ── 3b. 构建前端镜像 ──
FRONTEND_IMG_HASH_FILE="$CACHE_DIR/frontend-img.hash"
# 前端镜像 hash = Dockerfile + nginx.conf + dist/ 目录内容
CURRENT_FRONTEND_IMG_HASH=$(
    { file_md5 "$SCRIPT_DIR/deployment/frontend/Dockerfile" 2>/dev/null;
      file_md5 "$SCRIPT_DIR/deployment/frontend/nginx.conf" 2>/dev/null;
      dir_hash "$SCRIPT_DIR/dist"; } | pipe_md5
)
CACHED_FRONTEND_IMG_HASH=$(cat "$FRONTEND_IMG_HASH_FILE" 2>/dev/null || echo "")

if docker image inspect prison-frontend:latest &>/dev/null && [ "$CURRENT_FRONTEND_IMG_HASH" = "$CACHED_FRONTEND_IMG_HASH" ]; then
    echo "  前端镜像无需重建，使用缓存"
else
    echo "  正在构建前端镜像..."
    if ! docker build --platform linux/amd64 -f deployment/frontend/Dockerfile -t prison-frontend:latest .; then
        echo "错误: 前端镜像构建失败"
        exit 1
    fi
    echo "$CURRENT_FRONTEND_IMG_HASH" > "$FRONTEND_IMG_HASH_FILE"
    echo "  前端镜像构建完成"
fi

# ── 4. 导出镜像 ──
echo ""
echo "[4/5] 导出 Docker 镜像..."

mkdir -p "$DEPLOY_DIR"

# 验证两个镜像都存在
if ! docker image inspect prison-backend:latest &>/dev/null; then
    echo "错误: prison-backend:latest 镜像不存在"
    exit 1
fi
if ! docker image inspect prison-frontend:latest &>/dev/null; then
    echo "错误: prison-frontend:latest 镜像不存在"
    exit 1
fi

# 检查是否需要重新导出
APP_IMAGES_HASH_FILE="$CACHE_DIR/app-images.hash"
CURRENT_APP_HASH="$(docker inspect prison-backend:latest --format='{{.Id}}')$(docker inspect prison-frontend:latest --format='{{.Id}}')"
CACHED_APP_HASH=$(cat "$APP_IMAGES_HASH_FILE" 2>/dev/null || echo "")

if [ "$CURRENT_APP_HASH" = "$CACHED_APP_HASH" ] && [ -f "$DEPLOY_DIR/app-images.tar" ]; then
    echo "  应用镜像未变化，跳过导出"
else
    echo "  导出应用镜像..."
    docker save prison-backend:latest prison-frontend:latest -o "$DEPLOY_DIR/app-images.tar"
    echo "$CURRENT_APP_HASH" > "$APP_IMAGES_HASH_FILE"
    echo "  应用镜像导出完成: $(du -sh "$DEPLOY_DIR/app-images.tar" | cut -f1)"
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

cp "$SCRIPT_DIR/server/config/cameras.yml" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/install.sh" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/update.sh" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/.env" "$DEPLOY_DIR/"
cp "$SCRIPT_DIR/deployment/frontend/nginx.conf" "$DEPLOY_DIR/"
chmod +x "$DEPLOY_DIR/install.sh" "$DEPLOY_DIR/update.sh"

# 读取 .env 中的 FRONTEND_PORT，更新 nginx.conf 端口
FRONTEND_PORT=$(grep -E '^FRONTEND_PORT=' "$SCRIPT_DIR/deployment/.env" 2>/dev/null | cut -d'=' -f2 | tr -d '[:space:]')
FRONTEND_PORT=${FRONTEND_PORT:-8080}
if [ -f "$DEPLOY_DIR/nginx.conf" ]; then
    # 替换 listen 端口（兼容任意端口号）
    sed -i.bak "s/listen       [0-9]*/listen       $FRONTEND_PORT/" "$DEPLOY_DIR/nginx.conf"
    rm -f "$DEPLOY_DIR/nginx.conf.bak"
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
