# multitenant-backend

基于[vue-fastapi-admin](https://github.com/mizhexiaoxiao/vue-fastapi-admin)项目，使用FastAPI、SQLAlchemy重构后端实现多租户隔离。

开发中...

## 功能特点

- 使用PostgreSQL Schema实现多租户数据隔离
- RBAC权限控制
- 租户级别的菜单和API权限管理
- 审计日志功能
- 用户认证和授权
- 配置化管理

## 技术栈

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic

## 安装

1. 克隆项目
```bash
git clone https://github.com/Q-esperion/multitenant-backend.git
cd multitenant-backend
```

2. 安装 uv
```bash
pip install uv
```

3. 创建虚拟环境并安装依赖
```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

4. 配置环境变量
复制`.env.example`文件为`.env`并修改配置：
```bash
cp .env.example .env
```

5. 初始化数据库
```bash
alembic upgrade head
```

## 运行

```bash
uvicorn app.main:app --reload
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc


## 测试

### 租户隔离测试

运行租户数据隔离测试脚本：
```bash
python scripts/test_tenant_isolation.py
```

该脚本会：
1. 创建两个测试租户（AA租户和BB租户）
2. 为每个租户创建管理员用户
3. 测试租户间的数据隔离
4. 测试权限控制

## 项目结构

```
multi-tenant-backend/
├── alembic/              # 数据库迁移
├── app/
│   ├── api/             # API路由
│   ├── core/            # 核心配置
│   ├── db/              # 数据库
│   ├── models/          # 数据模型
│   └── schemas/         # Pydantic模型
├── docs/                # API文档
├── scripts/             # 测试脚本
├── tests/               # 测试
├── .env                 # 环境变量
├── .env.example         # 环境变量示例
├── pyproject.toml       # 项目配置和依赖管理
└── README.md           # 项目说明
```

## 数据库设计

### 公共Schema (public)
- tenants: 租户信息
- users: 用户信息
- roles: 角色信息
- menus: 菜单信息
- apis: API信息
- tenant_permissions: 租户权限

### 租户Schema (tenant_{id})
- 租户数据表


## License

MIT 