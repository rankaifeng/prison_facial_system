#!/bin/bash
#
# 监狱管控平台 - 联网部署脚本
# 用法: sudo bash install-online.sh
# 前提: 服务器可以连接外网，项目源码已拷贝到服务器
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 项目根目录（deployment 的上级目录）
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/prison_system"

echo ""
echo "============================================"
echo "   监狱关押罪犯出入管控平台 - 联网部署"
echo "============================================"
echo ""

# ── 读取配置 ──
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "错误: 未找到 .env 配置文件"
    echo "请先编辑 deployment/.env 填写服务器 IP"
    exit 1
fi

source "$SCRIPT_DIR/.env"

if [ "$SERVER_IP" = "192.168.x.x" ] || [ -z "$SERVER_IP" ]; then
    echo "错误: 请先编辑 .env 文件，填写 SERVER_IP"
    echo ""
    echo "查看服务器 IP: ip addr show | grep 'inet '"
    echo "然后编辑: nano $SCRIPT_DIR/.env"
    exit 1
fi

echo "配置信息:"
echo "  服务器 IP:   $SERVER_IP"
echo "  MySQL 密码:  $MYSQL_PASSWORD"
echo "  API 地址:    $RTI_API_BASE"
echo ""
read -p "确认以上信息正确？回车继续，Ctrl+C 取消 " _
echo ""

# ════════════════════════════════════════════
#  步骤 1: 安装 Docker
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 1/6: 安装 Docker"
echo "══════════════════════════════════════════"

if command -v docker &>/dev/null; then
    echo "  Docker 已安装，跳过"
else
    echo "  Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $USER 2>/dev/null || true
    echo "  Docker 安装完成: $(docker --version)"
fi

if ! docker info &>/dev/null; then
    systemctl start docker
    sleep 3
    if ! docker info &>/dev/null; then
        echo "  错误: Docker 启动失败"
        exit 1
    fi
fi
echo "  Docker 运行正常"
echo ""

# ════════════════════════════════════════════
#  步骤 2: 安装 Node.js（构建前端需要）
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 2/6: 检查 Node.js"
echo "══════════════════════════════════════════"

if command -v node &>/dev/null; then
    echo "  Node.js 已安装: $(node --version)"
else
    echo "  Node.js 未安装，正在安装..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    echo "  Node.js 安装完成: $(node --version)"
fi
echo ""

# ════════════════════════════════════════════
#  步骤 3: 拉取基础镜像
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 3/6: 拉取基础镜像"
echo "══════════════════════════════════════════"

docker pull mysql:8.0
docker pull redis:7-alpine
echo "  基础镜像拉取完成"
echo ""

# ════════════════════════════════════════════
#  步骤 4: 构建前端
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 4/6: 构建前端"
echo "══════════════════════════════════════════"

cd "$PROJECT_DIR"
npm install --silent
npm run build

if [ ! -d "$PROJECT_DIR/dist" ]; then
    echo "错误: 前端构建失败，未生成 dist 目录"
    exit 1
fi
echo "  前端构建完成"
echo ""

# ════════════════════════════════════════════
#  步骤 5: 构建 Docker 镜像并启动服务
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 5/6: 构建镜像并启动服务"
echo "══════════════════════════════════════════"

echo "  构建后端镜像..."
docker build -f "$PROJECT_DIR/server/Dockerfile" -t prison-backend:latest "$PROJECT_DIR"

echo "  构建前端镜像..."
docker build -f "$PROJECT_DIR/deployment/frontend/Dockerfile" -t prison-frontend:latest "$PROJECT_DIR"

mkdir -p "$INSTALL_DIR"

# 生成 SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 32)

# 生成 docker-compose.yml
cat > "$INSTALL_DIR/docker-compose.yml" << COMPOSEEOF
services:
  backend:
    image: prison-backend:latest
    container_name: prison-backend
    command: ["/app/deployment-entrypoint.sh"]
    restart: always
    environment:
      - DEBUG=False
      - SECRET_KEY=$SECRET_KEY
      - ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_NAME=prison_system
      - DB_USER=root
      - DB_PASSWORD=$MYSQL_PASSWORD
      - REDIS_URL=redis://redis:6379/0
      - RTI_API_BASE=$RTI_API_BASE
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - media-data:/app/media
      - ./cameras.yml:/app/config/cameras.yml
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - prison-network

  celery-beat:
    image: prison-backend:latest
    container_name: prison-celery-beat
    command: ["/app/celery-entrypoint.sh"]
    restart: always
    environment:
      - DEBUG=False
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_NAME=prison_system
      - DB_USER=root
      - DB_PASSWORD=$MYSQL_PASSWORD
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - prison-network

  frontend:
    image: prison-frontend:latest
    container_name: prison-frontend
    restart: always
    ports:
      - "${FRONTEND_PORT:-80}:80"
    depends_on:
      - backend
    networks:
      - prison-network

  mysql:
    image: mysql:8.0
    container_name: prison-mysql
    restart: always
    environment:
      - MYSQL_ROOT_PASSWORD=$MYSQL_PASSWORD
      - MYSQL_DATABASE=prison_system
      - MYSQL_CHARACTER_SET_SERVER=utf8mb4
      - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$MYSQL_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
    networks:
      - prison-network

  redis:
    image: redis:7-alpine
    container_name: prison-redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - prison-network

networks:
  prison-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
  media-data:
COMPOSEEOF

# 复制摄像头配置
if [ -f "$PROJECT_DIR/server/config/cameras.yml" ]; then
    cp "$PROJECT_DIR/server/config/cameras.yml" "$INSTALL_DIR/"
    echo "  摄像头配置已复制"
fi

echo "  启动服务..."
cd "$INSTALL_DIR"
docker compose up -d 2>&1 | sed 's/^/    /'

echo ""
echo "  等待 MySQL 初始化（约 30 秒）..."
for i in $(seq 1 30); do
    if docker exec prison-mysql mysqladmin ping -h localhost -u root -p"$MYSQL_PASSWORD" &>/dev/null 2>&1; then
        echo "  MySQL 已就绪"
        break
    fi
    printf "\r  等待中... %d/30" "$i"
    sleep 1
done
echo ""

echo "  等待后端完成数据库迁移..."
sleep 10

echo "  服务状态:"
docker compose ps 2>/dev/null | sed 's/^/    /'
echo ""

# ════════════════════════════════════════════
#  步骤 6: 创建管理员
# ════════════════════════════════════════════
echo "══════════════════════════════════════════"
echo "  步骤 6/6: 创建管理员账号"
echo "══════════════════════════════════════════"

echo ""
read -p "  请输入管理员用户名 (默认 admin): " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

read -s -p "  请输入管理员密码: " ADMIN_PASS
echo ""

if [ -z "$ADMIN_PASS" ]; then
    echo "  密码为空，跳过创建管理员"
    echo "  可稍后手动创建: docker exec -it prison-backend python manage.py createsuperuser"
else
    docker exec prison-backend python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(username='$ADMIN_USER').exists():
    u = User.objects.create_superuser('$ADMIN_USER', password='$ADMIN_PASS')
    print('OK')
else:
    print('EXISTS')
" 2>/dev/null && echo "  管理员创建成功" || echo "  管理员创建失败，请稍后手动创建"
fi

# ════════════════════════════════════════════
#  完成
# ════════════════════════════════════════════
echo ""
echo "============================================"
echo "   部署完成！"
echo "============================================"
echo ""
echo "   访问地址:  http://$SERVER_IP:${FRONTEND_PORT:-80}"
echo "   管理员:    $ADMIN_USER"
echo ""
echo "   常用命令:"
echo "     查看状态:  cd /opt/prison_system && docker compose ps"
echo "     查看日志:  cd /opt/prison_system && docker compose logs -f"
echo "     重启服务:  cd /opt/prison_system && docker compose restart"
echo "     停止服务:  cd /opt/prison_system && docker compose stop"
echo ""
