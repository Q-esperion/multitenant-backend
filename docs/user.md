# 用户管理接口文档

## 创建用户

```http
POST /api/v1/user/create
```

创建新用户。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "username": "string",
    "email": "string",
    "phone": "string",
    "password": "string",  // 加密后的密码，原始密码需满足以下规则：
                          // 1. 长度不能小于8位
                          // 2. 必须包含大写字母
                          // 3. 必须包含小写字母
                          // 4. 必须包含数字
                          // 5. 必须包含特殊字符
    "is_active": true,
    "is_superuser": false,
    "tenant_id": 1,
    "is_tenant_admin": false,
    "role_ids": [1, 2]  // 可选，用户角色ID列表
}
```

### 响应结果

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "id": 1,
        "username": "string",
        "email": "string",
        "phone": "string",
        "is_active": true,
        "is_superuser": false,
        "tenant_id": 1,
        "is_tenant_admin": false,
        "created_at": "2024-03-24T12:00:00",
        "updated_at": "2024-03-24T12:00:00",
        "roles": [
            {
                "id": 1,
                "name": "string"
            }
        ]
    }
}
```

### 错误码

- 400: 用户名已存在
- 400: 密码解密失败
- 400: 密码不符合规则（长度、大小写、数字、特殊字符）
- 403: 没有创建用户的权限
- 403: 租户管理员只能为自己租户创建用户
- 500: 创建用户失败

## 获取用户列表

```http
GET /api/v1/user/list
```

获取用户列表，支持分页和用户名搜索。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- page: 页码，默认1
- page_size: 每页数量，默认10，最大100
- username: 用户名搜索关键字（可选）
- email: 邮箱搜索关键字（可选）

### 响应结果

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "username": "string",
                "email": "string",
                "phone": "string",
                "is_active": true,
                "is_superuser": false,
                "tenant_id": 1,
                "is_tenant_admin": false,
                "created_at": "2024-03-24T12:00:00",
                "updated_at": "2024-03-24T12:00:00",
                "roles": [
                    {
                        "id": 1,
                        "name": "string"
                    }
                ]
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 10
    }
}
```

## 获取用户详情

```http
GET /api/v1/user/get
```

获取指定用户的详细信息。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- id: 用户ID

### 响应结果

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "id": 1,
        "username": "string",
        "email": "string",
        "phone": "string",
        "is_active": true,
        "is_superuser": false,
        "tenant_id": 1,
        "is_tenant_admin": false,
        "created_at": "2024-03-24T12:00:00",
        "updated_at": "2024-03-24T12:00:00",
        "roles": [
            {
                "id": 1,
                "name": "string"
            }
        ]
    }
}
```

### 错误码

- 404: 用户不存在

## 更新用户信息

```http
PUT /api/v1/user/update
```

更新指定用户的信息。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "id": 1,
    "username": "string",
    "email": "string",
    "phone": "string",
    "password": "string",
    "is_active": true,
    "is_superuser": false,
    "tenant_id": 1,
    "is_tenant_admin": false,
    "role_ids": [1, 2]
}
```

### 响应结果

```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "id": 1,
        "username": "string",
        "email": "string",
        "phone": "string",
        "is_active": true,
        "is_superuser": false,
        "tenant_id": 1,
        "is_tenant_admin": false,
        "created_at": "2024-03-24T12:00:00",
        "updated_at": "2024-03-24T12:00:00",
        "roles": [
            {
                "id": 1,
                "name": "string"
            }
        ]
        "message": "Updated Successfully"
    }
}
```

### 错误码

- 400: 密码解密失败
- 404: 用户不存在

## 删除用户

```http
DELETE /api/v1/user/delete
```

删除指定用户。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- id: 用户ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "User deleted successfully"
    }
}
```

### 错误码

- 404: 用户不存在

## 重置用户密码

```http
POST /api/v1/user/reset_password
```

重置指定用户的密码。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "id": "integer",
    "new_password": "string"  // 可选，加密后的新密码。如果不提供，将重置为默认密码
}
```

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "密码重置成功"  // 或 "密码已重置为默认密码（Admin@123456）"
    }
}
```

### 错误码

- 400: 密码解密失败
- 403: 没有重置密码的权限
- 403: 只能重置自己租户的用户密码
- 404: 用户不存在

## 权限说明

1. 超级管理员可以管理所有用户
2. 系统管理员可以管理所有租户的用户
3. 租户管理员只能管理自己租户的用户
4. 普通用户没有用户管理权限

## 注意事项

1. 所有接口都需要认证
2. 密码在传输前需要进行加密
3. 用户类型包括：
   - system_admin: 系统管理员
   - tenant_admin: 租户管理员
   - normal_user: 普通用户
4. 所有时间字段（created_at, updated_at）都以 ISO 格式返回 