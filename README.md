# 多租户校园新生报到系统

这是一个基于FastAPI和PostgreSQL的多租户校园新生报到系统后端。

## 功能特点

- 多租户数据隔离（使用PostgreSQL Schema）
- RBAC权限控制
- 租户级别的菜单和API权限管理
- 审计日志功能
- 部门管理
- 用户认证和授权
- 配置化管理

## 技术栈

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT认证
- Pydantic
- Alembic
- uv (Python包管理器)

## 安装

1. 克隆项目
```bash
git clone https://github.com/yourusername/multi-tenant-backend.git
cd multi-tenant-backend
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

详细的API文档请参考 `docs/` 目录下的文档：
- `docs/base.md`: 基础接口文档
- `docs/user.md`: 用户管理接口文档
- `docs/tenant.md`: 租户管理接口文档

## 密码规则

系统对用户密码有以下要求：
1. 长度不能小于8位
2. 必须包含大写字母
3. 必须包含小写字母
4. 必须包含数字
5. 必须包含特殊字符

示例密码：`Password123!`

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
- admission_batches: 入学批次
- departments: 部门信息
- students: 学生信息
- dormitories: 宿舍信息
- staff: 工作人员
- registration_processes: 报到流程
- registration_info: 报到信息
- field_mappings: 字段映射

## 开发工具

### 代码格式化
项目使用 Ruff 进行代码格式化和检查：
```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .
```

### 测试
项目使用 pytest 进行测试：
```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app
```

## 许可证

MIT 