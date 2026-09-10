# Django Backend Project

空的后端框架项目，基于 Django + MySQL + Redis。

## 快速开始

1. 创建虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 配置数据库和 Redis
```

4. 运行服务：
```bash
python manage.py runserver
```

## 项目结构

```
server/
├── config/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/            # 应用目录
├── manage.py
├── requirements.txt
└── .env.example
```
