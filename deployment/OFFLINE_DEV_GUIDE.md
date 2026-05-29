# 监狱面部识别系统 - 离线开发环境部署指南

## 一、离线安装包准备清单（在有网电脑上下载）

### 1.1 必须软件

| 软件 | 版本 | 下载地址 | 大小 | 用途 |
|------|------|----------|------|------|
| Docker Desktop | 4.x | https://docs.docker.com/desktop/install/windows-install/ | ~1GB | 后端服务 |
| Node.js | 18.x LTS | https://nodejs.org/dist/v18.20.0/node-v18.20.0-x64.msi | ~30MB | 前端开发 |
| Git for Windows | 2.x | https://git-scm.com/download/win | ~50MB | 版本控制 |

### 1.2 项目打包

```bash
# 在你的开发机器上执行
cd /path/to/prison_facial_system

# 1. 导出所有 Docker 镜像
cd deployment
docker save -o docker-images/prison-backend.tar prison-backend:latest
docker save -o docker-images/prison-frontend.tar prison-frontend:latest
docker save -o docker-images/prison-mysql.tar mysql:8.0
docker save -o docker-images/prison-redis.tar redis:7-alpine

# 2. 打包项目源码
cd ..
tar -czvf offline-deployment/project.tar.gz prison_facial_system/

# 3. 打包离线安装包
mkdir -p offline-deployment/software/{docker-desktop,nodejs,git}
# 把下载的安装包放入对应目录
```

---

## 二、目标电脑安装步骤

### 2.1 安装基础软件

```
1. 安装 Docker Desktop（约 1GB）
   - 双击 Docker Desktop Installer.exe
   - 勾选 "Use WSL 2 instead of Hyper-V"（推荐）
   - 安装完成后重启电脑

2. 安装 Node.js
   - 双击 node-v18.20.0-x64.msi
   - 默认安装即可
   - 验证：打开 PowerShell，输入 node -v

3. 安装 Git
   - 双击 Git-2.x.x-64-bit.exe
   - 建议勾选 "Git Bash Here"
   - 验证：打开 Git Bash，输入 git --version
```

### 2.2 导入 Docker 镜像

```powershell
# 管理员打开 PowerShell
cd C:\path\to\offline-deployment\docker-images

docker load -i prison-backend.tar
docker load -i prison-frontend.tar
docker load -i prison-mysql.tar
docker load -i prison-redis.tar

# 确认
docker images
```

### 2.3 解压项目源码

```powershell
cd C:\path\to\offline-deployment
tar -xzvf project.tar.gz
# 或用 7-Zip 右键解压
```

---

## 三、启动开发环境

### 3.1 启动后端服务（Docker）

```powershell
# 进入项目目录
cd C:\path\to\offline-deployment\prison_facial_system\deployment

# 启动所有后端服务
docker-compose up -d

# 等待 MySQL 启动完成（约 30 秒）
docker-compose logs mysql
# 看到 "ready for connections" 表示就绪

# 初始化数据库
docker exec -it prison-backend python manage.py migrate

# 创建管理员账户（可选）
docker exec -it prison-backend python manage.py createsuperuser
```

### 3.2 启动前端开发服务

```powershell
# 新开一个 PowerShell 窗口
cd C:\path\to\offline-deployment\prison_facial_system

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run dev
# 访问 http://localhost:3000
```

### 3.3 访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端开发页面 | http://localhost:3000 | 开发时访问 |
| 后端 API | http://localhost:8000 | API 接口 |
| Django Admin | http://localhost:8000/admin | 后台管理 |
| MySQL | localhost:3306 | 数据库 |

---

## 四、开发工作流

### 4.1 日常开发

```powershell
# 终端 1：启动后端 Docker 服务
cd project/deployment
docker-compose up -d

# 终端 2：启动前端开发服务
cd project
npm run dev
```

### 4.2 修改代码后

- **前端**：Vite 热更新自动生效
- **后端**：Django 代码修改后，`docker exec -it prison-backend python manage.py runserver 0.0.0.0:8000` 会自动重载
- **数据库**：迁移文件变更后执行 `docker exec -it prison-backend python manage.py migrate`

### 4.3 提交代码

```bash
cd project
git add .
git commit -m "你的提交信息"
git push  # 需要 VPN 或内网 git 服务器
```

---

## 五、文件传输建议

由于项目较大（node_modules 约 60MB），建议：

```
传输方式 1：U 盘拷贝（推荐）
- 软件安装包分开存
- 项目源码单独存

传输方式 2：局域网共享（如果有两台电脑在同一网络）
- 把 offline-deployment 放在共享文件夹
- 目标电脑直接访问

传输方式 3：移动硬盘
```

---

## 六、目录结构最终形态

```
C:\prison-system\
├── software\
│   ├── docker-desktop\     # Docker 安装包
│   ├── nodejs\             # Node.js 安装包
│   └── git\                # Git 安装包
├── docker-images\          # 导入的镜像
│   ├── prison-backend.tar
│   ├── prison-frontend.tar
│   ├── prison-mysql.tar
│   └── prison-redis.tar
├── project\                # 项目源码
│   ├── server\             # Django 后端
│   ├── src\                # React 前端
│   ├── deployment\          # Docker 配置
│   ├── package.json
│   └── node_modules\       # 依赖（可能已安装）
├── docker-compose.yml      # 直接放根目录方便操作
└── README.md               # 本文档
```

---

## 七、常见问题

### Q1: Docker Desktop 启动失败
```
解决：
1. 以管理员身份运行 Docker Desktop
2. 检查 WSL2 是否安装：wsl --list
3. 启用 WSL2：wsl --install
```

### Q2: npm install 失败（离线环境）
```
解决：
1. 确保 node_modules 已包含在项目打包中
2. 或使用国内镜像先下载好所有包
```

### Q3: 后端连接数据库失败
```
解决：
1. 等待 MySQL 完全启动（查看 docker-compose logs mysql）
2. 检查 .env 文件中 DB_HOST=mysql 是否正确
```

### Q4: 前端无法访问后端 API
```
解决：
检查 Vite 代理配置 vite.config.js 是否正确指向 localhost:8000
```

---

## 八、快速检查清单

```
[ ] Docker Desktop 已安装并运行
[ ] Node.js 已安装 (node -v 显示版本)
[ ] Git 已安装 (git --version 显示版本)
[ ] Docker 镜像已导入 (docker images 查看)
[ ] 数据库已迁移 (docker exec prison-backend python manage.py migrate)
[ ] npm 依赖已安装 (node_modules 存在)
[ ] 前后端服务已启动
```

按此清单检查，确保所有步骤完成后再进行开发。