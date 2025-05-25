# 日志管理接口文档

## 获取审计日志

```http
GET /api/v1/log/auditlog
```

获取系统审计日志，支持分页和多条件筛选。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- page: 页码，默认1
- page_size: 每页数量，默认10，最大100
- start_time: 开始时间（可选，ISO 8601格式）
- end_time: 结束时间（可选，ISO 8601格式）
- user_id: 用户ID（可选）
- action: 操作类型（可选）

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "user_id": "integer",
            "username": "string",
            "action": "string",
            "resource_type": "string",
            "resource_id": "integer",
            "detail": "string",
            "ip_address": "string",
            "user_agent": "string",
            "created_at": "string"  // ISO 格式的日期时间
        }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
}
```

## 获取访问日志

```http
GET /api/v1/log/accesslog
```

获取系统访问日志，支持分页和多条件筛选。

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

- page: 页码，默认1
- page_size: 每页数量，默认10，最大100
- start_time: 开始时间（可选，ISO 8601格式）
- end_time: 结束时间（可选，ISO 8601格式）
- user_id: 用户ID（可选）
- path: 访问路径（可选）

### 响应结果

```json
{
    "code": 200,
    "msg": "OK",
    "data": [
        {
            "id": "integer",
            "user_id": "integer",
            "username": "string",
            "method": "string",
            "path": "string",
            "status_code": "integer",
            "response_time": "float",
            "ip_address": "string",
            "user_agent": "string",
            "request_body": "string",
            "response_body": "string",
            "created_at": "string"  // ISO 格式的日期时间
        }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
}
```

## 权限说明

1. 超级管理员可以查看所有日志
2. 系统管理员可以查看所有日志
3. 租户管理员只能查看自己租户的日志
4. 普通用户只能查看自己的日志

## 注意事项

1. 所有接口都需要认证
2. 日志查询支持时间范围筛选
3. 审计日志记录用户的操作行为
4. 访问日志记录API的访问情况
5. 日志数据量可能较大，建议合理使用分页
6. 日志保留时间根据系统配置决定
7. 敏感信息在日志中会被脱敏处理
8. 日志查询结果按时间倒序排列
9. 所有时间字段都以 ISO 格式返回 