# 角色管理接口文档

## 获取角色列表

```http
GET /api/v1/role/list
```

获取角色列表，支持分页和角色名称搜索。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- page: 页码，默认1
- page_size: 每页数量，默认10，最大100
- role_name: 角色名称搜索关键字（可选）

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "tenant_id": "integer",
            "created_at": "string",  // ISO 格式的日期时间
            "updated_at": "string"   // ISO 格式的日期时间
        }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
}
```

## 获取角色详情

```http
GET /api/v1/role/get
```

获取指定角色的详细信息。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- role_id: 角色ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "id": "integer",
        "name": "string",
        "description": "string",
        "tenant_id": "integer",
        "created_at": "string",  // ISO 格式的日期时间
        "updated_at": "string"   // ISO 格式的日期时间
    }
}
```

### 错误码

- 404: 角色不存在

## 创建角色

```http
POST /api/v1/role/create
```

创建新的角色。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "name": "string",
    "description": "string"
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
        "description": "string",
        "tenant_id": "integer",
        "created_at": "string",  // ISO 格式的日期时间
        "updated_at": "string"   // ISO 格式的日期时间
    }
}
```

## 更新角色

```http
PUT /api/v1/role/update
```

更新指定角色的信息。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "role_id": "integer",
    "name": "string",        // 可选
    "description": "string"  // 可选
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

### 错误码

- 404: 角色不存在

## 删除角色

```http
DELETE /api/v1/role/delete
```

删除指定的角色。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- role_id: 角色ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "Role deleted successfully"
    }
}
```

### 错误码

- 404: 角色不存在

## 权限说明

1. 超级管理员可以管理所有租户的角色
2. 系统管理员可以管理所有租户的角色
3. 租户管理员只能管理自己租户的角色
4. 普通用户没有角色管理权限

## 注意事项

1. 所有接口都需要认证
2. 角色名称在同一租户内必须唯一
3. 删除角色操作不可恢复
4. 所有操作都会记录审计日志
5. 角色与租户是多对一的关系
6. 创建角色时会自动关联到当前用户的租户
7. 所有时间字段（created_at, updated_at）都以 ISO 格式返回 