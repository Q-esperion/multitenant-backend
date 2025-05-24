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

## 安装

1. 克隆项目
```bash
git clone https://github.com/yourusername/multi-tenant-backend.git
cd multi-tenant-backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
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
├── tests/               # 测试
├── .env                 # 环境变量
├── .env.example         # 环境变量示例
├── requirements.txt     # 项目依赖
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

## 许可证

MIT 