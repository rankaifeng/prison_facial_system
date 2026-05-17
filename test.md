# 监狱人脸识别系统 - 接口文档

## 一、系统概述

### 1.1 系统背景
本系统为监狱人脸识别系统，实现罪犯出监/入监的完整业务流程管理，包括人脸识别、信息采集、统计报表等功能。

### 1.2 业务流程

#### 出监流程
```
罪犯人脸打卡 → 档案库获取信息 → 出监确认表单(Step1:基本信息)
         ↓
前端从打卡机获取民警人脸 → 回显照片(Step2:民警确认)
         ↓
前端从打卡机获取特警人脸 → 回显照片(Step3:特警确认)
         ↓
前端从打卡机获取武警签名 → 保存图片(Step4:武警确认)
         ↓
一次性提交所有数据 → 数据库 → 首页统计更新
```

#### 入监流程
```
罪犯人脸打卡 → 档案库获取信息 → 入监确认表单(Step1:基本信息)
         ↓
前端从打卡机获取民警人脸 → 回显照片(Step2:民警确认)
         ↓
一次性提交所有数据 → 数据库 → 首页统计更新
```

**说明:** 民警/特警人脸照片、武警签名字段由前端从打卡机采集后，随提交一次性传给后端。

---

## 二、技术架构

### 2.1 技术栈
- **后端框架**: Django 4.2 + Django REST Framework
- **数据库**: MySQL
- **缓存**: Redis
- **认证**: JWT (JSON Web Token)

### 2.2 项目结构
```
server/
├── common/                 # 公共模块
│   ├── responses.py       # 统一响应格式
│   ├── exceptions.py      # 自定义异常
│   ├── decorators.py      # 公共装饰器
│   └── utils.py           # 工具函数
├── apps/users/
│   ├── models/            # 模型层
│   ├── repositories/      # 数据访问层
│   ├── services/          # 服务层（业务逻辑）
│   ├── controllers/       # 控制器层（HTTP处理）
│   └── serializers/        # 序列化器
└── config/                # 全局配置
```

### 2.3 四层架构职责

| 层级 | 职责 |
|------|------|
| Model | 数据表结构定义 |
| Repository | 数据增删改查，封装 SQL/ORM |
| Service | 业务逻辑处理 |
| Controller | HTTP 请求/响应处理 |

---

## 三、数据库设计

### 3.1 用户表 (user_login)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| username | VARCHAR(150) | 用户名（唯一） |
| password | VARCHAR(128) | 密码（加密） |
| first_name | VARCHAR(150) | 姓名 |
| role | VARCHAR(32) | 角色：admin/user |
| role_name | VARCHAR(64) | 角色名称 |
| prison_id | VARCHAR(32) | 所属分监区ID |
| prison_name | VARCHAR(128) | 所属分监区名称 |

### 3.2 出入记录表 (exit_entry_record)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| prisoner_no | VARCHAR(32) | 罪犯编号 |
| prisoner_name | VARCHAR(64) | 罪犯姓名 |
| prisoner_photo | VARCHAR(255) | 罪犯照片 |
| prison_area | VARCHAR(32) | 分监区ID |
| prison_area_name | VARCHAR(128) | 分监区名称 |
| type | VARCHAR(16) | 出监(exit) / 入监(entry) |
| reason | VARCHAR(32) | 出监原因 |
| exit_date | DATE | 出监日期 |
| entry_date | DATE | 入监日期 |
| police_face | VARCHAR(255) | 民警人脸照片路径 |
| police_name | VARCHAR(64) | 民警姓名 |
| swat_face | VARCHAR(255) | 特警人脸照片路径 |
| swat_name | VARCHAR(64) | 特警姓名 |
| armed_police_signature | TEXT | 武警签名(base64) |
| armed_police_name | VARCHAR(64) | 武警姓名 |
| operator_id | INT | 操作人ID |
| operator_name | VARCHAR(64) | 操作人姓名 |
| status | VARCHAR(16) | 状态：processing/completed |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.3 当日统计表 (daily_statistics)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| prison_area | VARCHAR(32) | 分监区ID |
| prison_area_name | VARCHAR(128) | 分监区名称 |
| date | DATE | 统计日期 |
| exit_count | INT | 出监总人数 |
| exit_reason_1 | INT | 刑满释放人数 |
| exit_reason_2 | INT | 外出就医人数 |
| exit_reason_3 | INT | 外出教育人数 |
| exit_reason_4 | INT | 离监探亲人数 |
| exit_reason_5 | INT | 押回重审人数 |
| entry_count | INT | 入监总人数 |
| in_prison_count | INT | 实时在监人数 |
| work_count | INT | 出工人数 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.4 历史统计表 (history_statistics)
字段同 `daily_statistics`，用于长期保存报表数据。

---

## 四、接口文档

### 4.1 基本信息
- **Base URL**: `http://localhost:8000/user_manage`
- **认证方式**: JWT Token
- **Content-Type**: `application/json`

### 4.2 通用响应格式
```json
{
  "code": 200,
  "message": "操作成功",
  "data": null
}
```

### 4.3 错误码说明
| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |

---

## 五、接口详情

### 认证模块

---

#### 5.1 用户登录
- **接口路径**: `POST /user_manage/user_login/user_login_web`
- **认证方式**: 无需认证

**请求参数 (application/json):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例（成功）:**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "id": 1,
    "username": "admin",
    "name": "admin",
    "role": "admin",
    "role_name": "管理员",
    "prison_id": "",
    "prison_name": ""
  }
}
```

**响应示例（失败）:**
```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

---

### 账号管理模块

> 以下接口需要管理员权限（role=admin）

---

#### 5.2 获取账号列表
- **接口路径**: `GET /user_manage/account/account_list`
- **认证方式**: Bearer Token (JWT) + 管理员权限

**请求参数:** 无

**响应示例:**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "username": "admin",
      "name": "admin",
      "role": "admin",
      "role_name": "管理员",
      "prison_id": "",
      "prison_name": "",
      "status": "active"
    }
  ],
  "num": 1
}
```

---

#### 5.3 创建账号
- **接口路径**: `POST /user_manage/account/account_add`
- **认证方式**: Bearer Token (JWT) + 管理员权限

**请求参数 (application/json):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 否 | 密码（默认 123456） |
| name | string | 否 | 姓名 |
| role | string | 否 | 角色（admin/user，默认 user） |
| prison_id | string | 否 | 所属分监区ID |
| prison_name | string | 否 | 所属分监区名称 |

**请求示例:**
```json
{
  "username": "zhangsan",
  "password": "123456",
  "name": "张三",
  "role": "user",
  "prison_id": "area1",
  "prison_name": "分监区一"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "新增成功",
  "data": {
    "id": 2,
    "username": "zhangsan",
    "name": "张三",
    "role": "user",
    "role_name": "普通用户",
    "prison_id": "area1",
    "prison_name": "分监区一"
  }
}
```

---

#### 5.4 删除账号
- **接口路径**: `POST /user_manage/account/account_delete`
- **认证方式**: Bearer Token (JWT) + 管理员权限

**请求参数 (application/json):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | int | 是 | 账号ID |

**请求示例:**
```json
{
  "id": 2
}
```

**响应示例（成功）:**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

**响应示例（失败 - 账号不存在）:**
```json
{
  "code": 404,
  "message": "账号不存在",
  "data": null
}
```

**响应示例（失败 - 不能删除管理员）:**
```json
{
  "code": 400,
  "message": "不能删除管理员账号",
  "data": null
}
```

---

### 出入监记录模块

> 以下接口需要登录认证（JWT Token）

---

#### 5.5 提交出监记录
- **接口路径**: `POST /user_manage/exit_record/submit`
- **认证方式**: Bearer Token (JWT)

**请求参数 (application/json):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| prisoner_no | string | 是 | 罪犯编号 |
| prisoner_name | string | 是 | 罪犯姓名 |
| prisoner_photo | string | 否 | 罪犯照片URL |
| prison_area | string | 是 | 分监区ID |
| prison_area_name | string | 是 | 分监区名称 |
| exit_date | string | 是 | 出监日期（YYYY-MM-DD） |
| reason | string | 是 | 出监原因 |
| police_face | string | 是 | 民警人脸图片（base64） |
| swat_face | string | 是 | 特警人脸图片（base64） |
| armed_police_signature | string | 是 | 武警签名图片（base64） |

**出监原因 (reason) 可选值:**
- `刑满释放`
- `外出就医`
- `外出教育`
- `离监探亲`
- `押回重审`

**请求示例:**
```json
{
  "prisoner_no": "P20240001",
  "prisoner_name": "李四",
  "prison_area": "area1",
  "prison_area_name": "分监区一",
  "exit_date": "2026-05-15",
  "reason": "刑满释放",
  "police_face": "base64encodedstring...",
  "swat_face": "base64encodedstring...",
  "armed_police_signature": "base64encodedstring..."
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "提交成功",
  "data": {
    "id": 1,
    "status": "completed"
  }
}
```

**业务逻辑说明:**
- 提交后自动创建出监记录
- 自动更新 `daily_statistics` 表中对应分监区当日出监人数 +1
- 自动更新 `daily_statistics` 表中对应分监区实时在监人数 -1
- 自动更新对应出监原因的统计字段 +1

---

#### 5.6 提交入监记录
- **接口路径**: `POST /user_manage/entry_record/submit`
- **认证方式**: Bearer Token (JWT)

**请求参数 (application/json):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| prisoner_no | string | 是 | 罪犯编号 |
| prisoner_name | string | 是 | 罪犯姓名 |
| prisoner_photo | string | 否 | 罪犯照片URL |
| prison_area | string | 是 | 分监区ID |
| prison_area_name | string | 是 | 分监区名称 |
| entry_date | string | 是 | 入监日期（YYYY-MM-DD） |
| police_face | string | 是 | 民警人脸图片（base64） |

**请求示例:**
```json
{
  "prisoner_no": "P20240002",
  "prisoner_name": "王五",
  "prison_area": "area1",
  "prison_area_name": "分监区一",
  "entry_date": "2026-05-15",
  "police_face": "base64encodedstring..."
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "提交成功",
  "data": {
    "id": 2,
    "status": "completed"
  }
}
```

**业务逻辑说明:**
- 提交后自动创建入监记录
- 自动更新 `daily_statistics` 表中对应分监区当日入监人数 +1
- 自动更新 `daily_statistics` 表中对应分监区实时在监人数 +1

---

#### 5.7 获取出入记录列表
- **接口路径**: `GET /user_manage/record/list`
- **认证方式**: Bearer Token (JWT)

**请求参数 (Query):**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | string | 否 | 记录类型（exit/entry） |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| prison_area | string | 否 | 分监区ID |
| page | int | 否 | 页码（默认 1） |
| page_size | int | 否 | 每页数量（默认 10） |

**请求示例:**
```
GET /user_manage/record/list?type=exit&start_date=2026-05-01&end_date=2026-05-15&page=1&page_size=10
```

**响应示例:**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "prisoner_no": "P20240001",
      "prisoner_name": "李四",
      "prison_area_name": "分监区一",
      "type": "exit",
      "reason": "刑满释放",
      "exit_date": "2026-05-15",
      "entry_date": null,
      "status": "completed",
      "created_at": "2026-05-15 10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

---

### 统计报表模块

> 以下接口需要登录认证（JWT Token）

---

#### 5.8 获取实时统计
- **接口路径**: `GET /user_manage/statistics/realtime`
- **认证方式**: Bearer Token (JWT)

**请求参数:** 无

**响应示例:**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 1,
    "exit_count": 2,
    "entry_count": 1,
    "exit_reason_1": 1,
    "exit_reason_2": 1,
    "exit_reason_3": 0,
    "exit_reason_4": 0,
    "exit_reason_5": 0
  }
}
```

**字段说明:**
| 字段 | 说明 |
|------|------|
| total | 出监净人数 = 出监总人数 - 入监总人数 |
| exit_count | 出监总人数（累计） |
| entry_count | 入监总人数（累计） |
| exit_reason_1 | 刑满释放人数 |
| exit_reason_2 | 外出就医人数 |
| exit_reason_3 | 外出教育人数 |
| exit_reason_4 | 离监探亲人数 |
| exit_reason_5 | 押回重审人数 |

**业务逻辑说明:**
- 管理员可查看所有分监区的统计数据
- 普通用户只能查看自己所属分监区的统计数据
- total = exit_count - entry_count，即出监后还未返回的人数

---

#### 5.9 获取劳动统计
- **接口路径**: `GET /user_manage/statistics/work`
- **认证方式**: Bearer Token (JWT)

**请求参数:** 无

**响应示例:**
```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "date": "2026-05-15",
      "total": 10,
      "workCount": 8
    }
  ]
}
```

---

## 六、角色权限

| 角色 | 说明 | 权限 |
|------|------|------|
| admin | 管理员 | 全部权限，包括账号管理 |
| user | 普通用户 | 查看统计、提交出入监记录 |

**说明:** 系统只有两个角色，operator（操作员）和 manager（经理）已移除。

---

## 七、认证流程

1. 调用登录接口 `POST /user_manage/user_login/user_login_web`，获取 token
2. 在后续请求的 Header 中添加 `Authorization: Bearer <token>`
3. token 有效期为 24 小时

**示例:**
```bash
curl -X GET "http://localhost:8000/user_manage/statistics/realtime" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## 八、分监区列表

| prison_id | prison_area_name |
|-----------|------------------|
| area1 | 分监区一 |
| area2 | 分监区二 |
| area3 | 分监区三 |
| area4 | 分监区四 |
| area5 | 分监区五 |
| area6 | 分监区六 |
| area7 | 分监区七 |

---

## 九、错误信息

| code | message | 说明 |
|------|---------|------|
| 400 | 参数错误 | 请求参数格式不正确 |
| 400 | 缺少必要参数 | 缺少必需参数 |
| 400 | 账号已存在 | 新增账号时用户名重复 |
| 400 | 不能删除管理员账号 | 禁止删除 admin 账号 |
| 401 | 身份认证信息未提供 | 未携带 token |
| 401 | 无效的 token | token 已过期或无效 |
| 401 | 用户名或密码错误 | 登录失败 |
| 403 | 无权限访问 | 当前用户无此接口权限 |
| 404 | 账号不存在 | 删除账号时 ID 不存在 |

---

## 十、启动服务

```bash
cd server
python3 manage.py runserver
```

服务将运行在 `http://localhost:8000`