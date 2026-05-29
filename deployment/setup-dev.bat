@echo off
chcp 65001 >nul
echo ========================================
echo   监狱系统 - 开发环境一键初始化
echo ========================================
echo.

echo [1/6] 检查 Docker 状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker 运行正常
echo.

echo [2/6] 导入 Docker 镜像（首次运行需要）...
if exist "docker-images\prison-backend.tar" (
    docker load -i docker-images\prison-backend.tar >nul 2>&1
    echo [OK] prison-backend
)
if exist "docker-images\prison-frontend.tar" (
    docker load -i docker-images\prison-frontend.tar >nul 2>&1
    echo [OK] prison-frontend
)
if exist "docker-images\prison-mysql.tar" (
    docker load -i docker-images\prison-mysql.tar >nul 2>&1
    echo [OK] MySQL
)
if exist "docker-images\prison-redis.tar" (
    docker load -i docker-images\prison-redis.tar >nul 2>&1
    echo [OK] Redis
)
echo.

echo [3/6] 启动 Docker 服务（MySQL + Redis + Backend）...
docker-compose up -d
echo [OK] 服务已启动
echo.

echo [4/6] 等待 MySQL 就绪（约 30 秒）...
echo 正在等待 MySQL 启动，请稍候...
timeout /t 30 /nobreak >nul
echo [OK] 等待完成
echo.

echo [5/6] 检查服务状态...
docker-compose ps
echo.

echo [6/6] 初始化数据库（首次运行需要）...
docker exec -it prison-backend python manage.py migrate >nul 2>&1
if errorlevel 1 (
    echo [跳过] 数据库迁移已完成或无需迁移
) else (
    echo [OK] 数据库迁移完成
)
echo.

echo ========================================
echo   环境初始化完成！
echo ========================================
echo.
echo 【启动服务】
echo   后端（Docker）：docker-compose up -d
echo   前端（开发）：npm run dev
echo.
echo 【访问地址】
echo   前端页面：http://localhost:3000
echo   后端 API：http://localhost:8000
echo   Django Admin：http://localhost:8000/admin
echo.
echo 按任意键退出...
pause >nul