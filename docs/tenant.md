# 租户管理接口文档

## 获取租户列表

```http
GET /api/v1/tenant/list
```

获取所有租户的列表，支持分页。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- page: 页码，默认1
- page_size: 每页数量，默认10，最大100

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "name": "string",
            "schema_name": "string",
            "status": "string",
            "description": "string",
            "max_users": "integer",
            "expire_date": "string",  // ISO 格式的日期时间
            "created_at": "string",   // ISO 格式的日期时间
            "updated_at": "string"    // ISO 格式的日期时间
        }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
}
```

## 创建租户

```http
POST /api/v1/tenant/create
```

创建新的租户，并自动创建租户相关的数据库表。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "name": "string",
    "description": "string",
    "max_users": "integer",
    "expire_date": "string"  // ISO 8601格式的日期
}
```

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "id": "integer",
        "name": "string",
        "schema_name": "string",
        "status": "string",
        "description": "string",
        "max_users": "integer",
        "expire_date": "string",  // ISO 格式的日期时间
        "created_at": "string",   // ISO 格式的日期时间
        "updated_at": "string"    // ISO 格式的日期时间
    }
}
```

### 创建的表结构

创建租户时会自动创建以下表：

1. admission_batches（招生批次表）
   - id: 主键
   - name: 批次名称
   - start_date: 开始日期
   - end_date: 结束日期
   - is_active: 是否激活
   - description: 描述

2. departments（院系表）
   - id: 主键
   - name: 院系名称
   - code: 院系代码
   - parent_id: 父级院系ID
   - order: 排序
   - leader: 负责人
   - phone: 联系电话
   - email: 邮箱
   - status: 状态

3. dormitories（宿舍表）
   - id: 主键
   - building: 楼栋
   - room_number: 房间号
   - capacity: 容量
   - current_count: 当前人数
   - status: 状态

4. students（学生表）
   - id_card: 身份证号（主键）
   - student_id: 学号
   - name: 姓名
   - gender: 性别
   - birth_date: 出生日期
   - admission_batch_id: 招生批次ID
   - department_id: 院系ID
   - dormitory_id: 宿舍ID
   - phone: 电话
   - email: 邮箱
   - address: 地址
   - status: 状态
   - ext_field1-10: 扩展字段

5. staff（教职工表）
   - id: 主键
   - username: 用户名
   - password: 密码
   - name: 姓名
   - gender: 性别
   - phone: 电话
   - email: 邮箱
   - department_id: 部门ID
   - position: 职位
   - status: 状态

6. registration_processes（注册流程表）
   - id: 主键
   - name: 流程名称
   - order: 排序
   - description: 描述
   - is_required: 是否必需
   - status: 状态

7. info_entry_processes（信息录入流程表）
   - id: 主键
   - name: 流程名称
   - order: 排序
   - description: 描述
   - is_required: 是否必需
   - status: 状态

8. registration_info（注册信息表）
   - id: 主键
   - student_id: 学生ID
   - process_id: 流程ID
   - status: 状态
   - completed_at: 完成时间
   - operator_id: 操作人ID

## 更新租户信息

```http
PUT /api/v1/tenant/update
```

更新指定租户的信息。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "tenant_id": "integer",
    "name": "string",        // 可选
    "description": "string", // 可选
    "max_users": "integer",  // 可选
    "expire_date": "string", // 可选，ISO 8601格式的日期
    "status": "string"       // 可选，ACTIVE/INACTIVE
}
```

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "Updated Successfully"
    }
}
```

## 删除租户

```http
DELETE /api/v1/tenant/delete
```

删除指定的租户。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- tenant_id: 租户ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "Tenant deleted successfully"
    }
}
```

## 权限说明

1. 只有超级管理员可以管理租户
2. 系统管理员和租户管理员没有租户管理权限
3. 普通用户没有租户管理权限

## 注意事项

1. 所有接口都需要认证
2. 租户名称必须唯一
3. 删除租户操作不可恢复
4. 所有操作都会记录审计日志
5. 创建租户时会自动创建相关的数据库表
6. 所有时间字段（created_at, updated_at, expire_date）都以 ISO 格式返回 