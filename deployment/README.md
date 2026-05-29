# 监狱面部识别系统 - 离线 Docker 部署指南

## 目录结构

```
prison_facial_system/
├── deployment/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── docker-compose.yml
│   └── README.md
├── server/          (后端代码)
└── src/            (前端代码)
```

---

## 第一阶段：有网机器上准备（在你的开发机器上执行）

### 步骤 1：构建前端

```bash
cd prison_facial_system
npm run build
```

### 步骤 2：构建后端镜像

```bash
cd prison_facial_system/deployment

# 构建后端镜像
docker build -t prison-backend:latest ./backend

# 构建前端镜像
docker build -t prison-frontend:latest ./frontend
```

### 步骤 3：导出镜像

```bash
# 导出所有镜像为 tar 文件
docker save -o prison-backend.tar prison-backend:latest
docker save -o prison-frontend.tar prison-frontend:latest
docker save -o prison-mysql.tar mysql:8.0
docker save -o prison-redis.tar redis:7-alpine

# 打包到一个文件夹
mkdir offline-packages
mv *.tar offline-packages/
```

### 步骤 4：拷贝到 U 盘

```
offline-packages/
├── prison-backend.tar
├── prison-frontend.tar
├── prison-mysql.tar
├── prison-redis.tar
└── docker-compose.yml
```

---

## 第二阶段：目标电脑离线部署

### 前提条件

目标 Windows 电脑需要提前安装 **Docker Desktop**：
- 下载离线安装包：https://docs.docker.com/desktop/install/windows-install/
- 安装包约 1GB，需在有网环境下载

### 步骤 1：导入 Docker 镜像

```powershell
# 管理员运行 PowerShell
cd C:\path\to\offline-packages

docker load -i prison-backend.tar
docker load -i prison-frontend.tar
docker load -i prison-mysql.tar
docker load -i prison-redis.tar

# 确认镜像加载成功
docker images
```

### 步骤 2：启动服务

```powershell
# 确保 docker-compose.yml 在当前目录
docker-compose up -d

# 查看运行状态
docker-compose ps
```

### 步骤 3：初始化数据库

```powershell
# 进入后端容器执行迁移
docker exec -it prison-backend python manage.py migrate

# 创建超级管理员（可选）
docker exec -it prison-backend python manage.py createsuperuser
```

### 步骤 4：访问系统

打开浏览器访问：**http://localhost**

---

## 验证部署成功

```powershell
# 检查所有容器状态
docker-compose ps

# 查看后端日志
docker-compose logs backend

# 查看前端日志
docker-compose logs frontend
```

---

## 常见问题

### 1. Docker Desktop 无法启动
```
尝试：以管理员身份运行 Docker Desktop
或者：检查 WSL2 是否安装正确
```

### 2. 端口冲突
```yaml
# 修改 docker-compose.yml 中的端口
ports:
  - "8080:80"    # 前端改成 8080
  - "3307:3306"  # MySQL 改成 3307
```

### 3. 数据库连接失败
```powershell
# 等待 MySQL 完全启动（约 30 秒）
docker-compose logs mysql
# 确认看到 "ready for connections" 后再试
```

---

## 数据持久化

所有数据存储在 Docker volumes 中：
- `mysql-data` - MySQL 数据库文件
- `./media` - 上传的文件

备份数据：
```powershell
docker-compose down
# 备份整个 deployment 文件夹
```

---

## 注意事项

1. **离线环境无法 Pull 新镜像**，所有镜像必须提前导入
2. 目标电脑首次启动 Docker 需要较大内存，建议 8GB+ RAM
3. 建议关闭不需要的程序以释放系统资源