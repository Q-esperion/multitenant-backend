# 菜单管理接口文档

## 获取菜单列表

```http
GET /api/v1/menu/list
```

获取当前租户的菜单列表，按排序字段排序。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- skip: 跳过的记录数，默认0
- limit: 返回的最大记录数，默认100

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "name": "string",
            "path": "string",
            "component": "string",
            "redirect": "string",
            "parent_id": "integer",
            "order": "integer",
            "icon": "string",
            "is_hidden": "boolean",
            "is_cache": "boolean",
            "tenant_id": "integer",
            "created_at": "string",  // ISO 格式的日期时间
            "updated_at": "string"   // ISO 格式的日期时间
        }
    ]
}
```

## 创建菜单

```http
POST /api/v1/menu/create
```

创建新的菜单项。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "name": "string",        // 菜单名称
    "path": "string",        // 路由路径
    "component": "string",   // 组件路径
    "redirect": "string",    // 重定向路径
    "parent_id": "integer",  // 父级菜单ID
    "order": "integer",      // 排序号
    "icon": "string",        // 图标
    "is_hidden": "boolean",  // 是否隐藏
    "is_cache": "boolean"    // 是否缓存
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
        "path": "string",
        "component": "string",
        "redirect": "string",
        "parent_id": "integer",
        "order": "integer",
        "icon": "string",
        "is_hidden": "boolean",
        "is_cache": "boolean",
        "tenant_id": "integer",
        "created_at": "string",  // ISO 格式的日期时间
        "updated_at": "string"   // ISO 格式的日期时间
    }
}
```

## 获取菜单详情

```http
GET /api/v1/menu/get
```

获取指定菜单的详细信息。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- id: 菜单ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "id": "integer",
        "name": "string",
        "path": "string",
        "component": "string",
        "redirect": "string",
        "parent_id": "integer",
        "order": "integer",
        "icon": "string",
        "is_hidden": "boolean",
        "is_cache": "boolean",
        "tenant_id": "integer",
        "created_at": "string",  // ISO 格式的日期时间
        "updated_at": "string"   // ISO 格式的日期时间
    }
}
```

### 错误码

- 404: 菜单不存在

## 更新菜单

```http
PUT /api/v1/menu/update
```

更新指定菜单的信息。

### 请求头

```
Authorization: Bearer <token>
```

### 请求参数

```json
{
    "id": "integer",
    "name": "string",        // 可选
    "path": "string",        // 可选
    "component": "string",   // 可选
    "redirect": "string",    // 可选
    "parent_id": "integer",  // 可选
    "order": "integer",      // 可选
    "icon": "string",        // 可选
    "is_hidden": "boolean",  // 可选
    "is_cache": "boolean"    // 可选
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

- 404: 菜单不存在

## 删除菜单

```http
DELETE /api/v1/menu/delete
```

删除指定的菜单（软删除）。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- id: 菜单ID

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": {
        "message": "Menu deleted successfully"
    }
}
```

### 错误码

- 404: 菜单不存在

## 权限说明

1. 超级管理员可以管理所有租户的菜单
2. 系统管理员可以管理所有租户的菜单
3. 租户管理员只能管理自己租户的菜单
4. 普通用户没有菜单管理权限

## 注意事项

1. 所有接口都需要认证
2. 菜单路径在同一租户内必须唯一
3. 删除菜单操作不可恢复
4. 所有操作都会记录审计日志
5. 菜单与租户是多对一的关系
6. 创建菜单时会自动关联到当前用户的租户
7. 所有时间字段（created_at, updated_at）都以 ISO 格式返回 