#!/bin/bash
# MySQL 安装和启动脚本

echo "=== 1. 安装 MySQL ==="
brew install mysql

echo "=== 2. 启动 MySQL 服务 ==="
brew services start mysql

echo "=== 3. 设置 root 密码 ==="
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';"

echo "=== 4. 创建数据库 ==="
mysql -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS prison_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "=== 5. 安装 Python 依赖 ==="
cd server
pip3 install -r requirements.txt

echo "=== 6. 运行迁移 ==="
python3 manage.py migrate

echo "=== 7. 启动 Django ==="
python3 manage.py runserver 0.0.0.0:8000
