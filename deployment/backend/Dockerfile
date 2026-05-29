FROM docker.1ms.run/library/python:3.9-slim

WORKDIR /app

# 安装系统依赖（MySQL 客户端需要）
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY ../server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY ../server/ .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]