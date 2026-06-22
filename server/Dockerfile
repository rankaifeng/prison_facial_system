FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖（MySQL 客户端 + FFmpeg）
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装（从 server/ 目录）
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（从 server/ 目录）
COPY server/ .

# 复制 entrypoint 脚本
COPY server/deployment-entrypoint.sh /app/deployment-entrypoint.sh
COPY server/celery-entrypoint.sh /app/celery-entrypoint.sh
RUN chmod +x /app/deployment-entrypoint.sh /app/celery-entrypoint.sh

# 收集静态文件
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
