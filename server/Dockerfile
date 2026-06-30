FROM docker.1ms.run/library/python:3.9-slim

WORKDIR /app

# 使用国内 Debian 镜像源
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖（这层很少变，会缓存）
RUN apt-get update && \
    apt-get install -f -y && \
    apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 先只复制 requirements.txt，单独安装依赖（依赖不变时这层也缓存）
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 最后复制代码（代码经常变，但这层很轻量）
COPY server/ .

# 复制 entrypoint 脚本
RUN cp /app/deployment-entrypoint.sh /app/deployment-entrypoint.sh 2>/dev/null || true && \
    cp /app/celery-entrypoint.sh /app/celery-entrypoint.sh 2>/dev/null || true && \
    chmod +x /app/deployment-entrypoint.sh /app/celery-entrypoint.sh 2>/dev/null || true

# 收集静态文件
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
