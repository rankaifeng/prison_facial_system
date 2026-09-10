# 监狱关押罪犯出入管控平台 - 部署文档

## 一共就两步

### 第一步：在你的电脑上（有网）

```bash
cd prison_facial_system
chmod +x prepare.sh
./prepare.sh
```

脚本会自动：构建前端 → 构建 Docker 镜像 → 导出镜像 → 打包所有依赖

完成后会生成一个 `deploy-package` 文件夹。

**把这个文件夹整个拷贝到 U 盘。**

### 第二步：在服务器上（无网）

1. 把 U 盘的 `deploy-package` 文件夹拷贝到服务器桌面

2. 修改配置：
```bash
cd ~/Desktop/deploy-package
nano .env
```
把 `SERVER_IP=192.168.x.x` 改成服务器实际 IP（用 `ip addr` 查看）

3. 运行安装脚本：
```bash
sudo bash install.sh
```

脚本会自动：安装 Docker → 导入镜像 → 启动所有服务 → 创建管理员

4. 完成后浏览器访问 `http://服务器IP`

---

## 日常运维

```bash
cd /opt/prison_system

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 停止
docker compose stop
```

## 摄像头配置

编辑 `/opt/prison_system/cameras.yml`，改完后：
```bash
cd /opt/prison_system
docker compose restart backend
```

## 数据备份

```bash
# 备份数据库
docker exec prison-mysql mysqldump -u root -p'Prison@2026' prison_system > /opt/backup_$(date +%Y%m%d).sql
```

## 更新版本

有网电脑重新运行 `./prepare.sh`，把新的 `app-images.tar` 拷到服务器：
```bash
docker load -i app-images.tar
cd /opt/prison_system && docker compose up -d
```
  1. U 盘拷 deploy-package 文件夹到服务器
  2. 改 .env 里的 SERVER_IP 为服务器实际 IP
  3. sudo bash install.sh