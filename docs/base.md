# 基础接口文档

## 认证相关接口

### 登录获取Token

```http
POST /api/v1/base/access_token
```

获取访问令牌，用于后续接口的认证。

#### 请求参数

```json
{
    "username": "string",
    "password": "string"  // 加密后的密码，原始密码需满足以下规则：
                         // 1. 长度不能小于8位
                         // 2. 必须包含大写字母
                         // 3. 必须包含小写字母
                         // 4. 必须包含数字
                         // 5. 必须包含特殊字符
}
```

#### 响应结果

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "access_token": "string",
        "token_type": "bearer"
    }
}
```

#### 错误码

- 400: 用户名或密码错误
- 400: 密码解密失败
- 400: 密码不符合规则
- 401: 用户未激活
- 500: 服务器错误

### 获取用户信息

```http
GET /api/v1/base/userinfo
```

获取当前登录用户的详细信息。

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应结果

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "phone": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "is_tenant_admin": "boolean",
        "tenant_id": "integer",
        "user_type": "string",
        "created_at": "string",  // ISO 格式的日期时间
        "updated_at": "string",  // ISO 格式的日期时间
        "roles": [
            {
                "id": "integer",
                "name": "string"
            }
        ]
    }
}
```

### 获取用户菜单

```http
GET /api/v1/base/usermenu
```

获取当前用户的菜单权限。

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "name": "string",
            "title": "string",
            "menu_type": "string",
            "path": "string",
            "component": "string",
            "icon": "string",
            "order": "integer",
            "parent_id": "integer",
            "is_hidden": "boolean",
            "keepalive": "boolean",
            "redirect": "string",
            "is_enabled": "boolean",
            "children": []
        }
    ]
}
```

### 获取用户API权限

```http
GET /api/v1/base/userapi
```

获取当前用户的API权限列表。

#### 请求头

```
Authorization: Bearer <token>
```

#### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": ["string"]  // API路径列表
}
```

### 修改密码

```http
POST /api/v1/base/update_password
```

修改当前用户的密码。

#### 请求头

```
Authorization: Bearer <token>
```

#### 请求参数

```json
{
    "old_password": "string",  // 加密后的旧密码
    "new_password": "string"   // 加密后的新密码
}
```

#### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "msg": "密码修改成功"
    }
}
```

#### 错误码

- 400: 密码解密失败
- 400: 旧密码错误
- 400: 新密码格式不正确

### 用户注册

```http
POST /api/v1/base/register
```

注册新用户。

#### 请求参数

```json
{
    "username": "string",
    "email": "string",
    "password": "string",  // 加密后的密码
    "tenant_id": "integer"
}
```

#### 响应结果

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "is_tenant_admin": "boolean",
        "tenant_id": "integer"
    }
}
```

### 创建用户（超级管理员）

```http
POST /api/v1/base/user/create
```

超级管理员创建新用户。

#### 请求头

```
Authorization: Bearer <token>
```

#### 请求参数

```json
{
    "username": "string",
    "email": "string",
    "password": "string",  // 加密后的密码
    "tenant_id": "integer",
    "is_active": "boolean",
    "is_superuser": "boolean",
    "is_tenant_admin": "boolean"
}
```

#### 响应结果

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "is_tenant_admin": "boolean",
        "tenant_id": "integer"
    }
}
```

## 注意事项

1. 所有需要认证的接口都需要在请求头中携带 `Authorization: Bearer <token>`
2. 密码在传输前需要进行加密
3. 所有时间字段（created_at, updated_at）都以 ISO 格式返回
4. 用户类型包括：
   - system_admin: 系统管理员
   - tenant_admin: 租户管理员
   - normal_user: 普通用户 