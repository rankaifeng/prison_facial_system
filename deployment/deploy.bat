@echo off
chcp 65001 >nul
echo ========================================
echo   监狱面部识别系统 - Docker 一键部署
echo ========================================
echo.

echo [1/4] 检查 Docker 状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker 运行正常
echo.

echo [2/4] 导入 Docker 镜像（首次运行需要）...
if exist "prison-backend.tar" (
    docker load -i prison-backend.tar
    echo [OK] prison-backend 镜像导入完成
) else (
    echo [跳过] prison-backend.tar 不存在
)

if exist "prison-frontend.tar" (
    docker load -i prison-frontend.tar
    echo [OK] prison-frontend 镜像导入完成
) else (
    echo [跳过] prison-frontend.tar 不存在
)

if exist "prison-mysql.tar" (
    docker load -i prison-mysql.tar
    echo [OK] MySQL 镜像导入完成
) else (
    echo [跳过] prison-mysql.tar 不存在
)

if exist "prison-redis.tar" (
    docker load -i prison-redis.tar
    echo [OK] Redis 镜像导入完成
) else (
    echo [跳过] prison-redis.tar 不存在
)

echo.
echo [3/4] 启动服务...
docker-compose up -d

echo.
echo [4/4] 等待服务启动（约 30 秒）...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo 访问地址：http://localhost
echo.
echo 常用命令：
echo   查看状态：docker-compose ps
echo   查看日志：docker-compose logs -f
echo   停止服务：docker-compose down
echo   初始化数据库：docker exec -it prison-backend python manage.py migrate
echo.
echo 按任意键退出...
pause >nul