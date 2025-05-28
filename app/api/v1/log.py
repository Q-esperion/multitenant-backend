from typing import Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from app.db.session import get_db
from app.deps import get_current_user, get_current_active_superuser
from app.models.public import User, AuditLog, AccessLog
from app.schemas.log import AuditLogResponse, AccessLogResponse
from app.schemas.common import Success, SuccessExtra
from app.utils.audit import log_audit

router = APIRouter()

@router.get("/list")
async def get_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: str = None,
    module: str = None,
    summary: str = None,
    method: str = None,
    path: str = None,
    status: str = None,
    start_time: str = None,
    end_time: str = None
) -> Any:
    """
    获取审计日志列表
    """
    # 构建基础查询
    query = select(AuditLog).join(User)
    
    # 添加搜索条件
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    if module:
        query = query.where(AuditLog.resource_type.ilike(f"%{module}%"))
    if summary:
        query = query.where(AuditLog.details.ilike(f"%{summary}%"))
    
    # 处理时间范围
    if start_time:
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        query = query.where(AuditLog.created_at >= start_datetime)
    if end_time:
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        query = query.where(AuditLog.created_at <= end_datetime)
    
    # 如果不是超级管理员，只能查看自己的日志
    if not current_user.is_superuser:
        query = query.where(AuditLog.user_id == current_user.id)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    log_list = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at,
            # 从 details 中解析额外信息
            "summary": log.details.split(":")[0] if log.details else None,
            "module": log.resource_type,
            "method": log.action.upper(),
            "path": f"/api/v1/{log.resource_type}/{log.action}",
            "status": 200,  # 默认状态码
            "request_args": {},  # 默认空对象
            "response_body": {},  # 默认空对象
            "response_time": 0.0  # 默认响应时间
        }
        log_list.append(AuditLogResponse.model_validate(log_dict))
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="log",
        resource_id=0,
        details=f"查询审计日志列表，筛选条件：用户名={username}, 模块={module}, 描述={summary}, 开始时间={start_time}, 结束时间={end_time}",
        request=request
    )
    
    return SuccessExtra(data=log_list, total=total, page=page, page_size=page_size)

@router.get("/get")
async def get_log(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取审计日志详情
    """
    query = select(AuditLog).join(User).where(AuditLog.id == id)
    
    # 如果不是超级管理员，只能查看自己的日志
    if not current_user.is_superuser:
        query = query.where(AuditLog.user_id == current_user.id)
    
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )
    
    # 构建响应数据
    log_dict = {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.user.username if log.user else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at,
        # 从 details 中解析额外信息
        "summary": log.details.split(":")[0] if log.details else None,
        "module": log.resource_type,
        "method": log.action.upper(),
        "path": f"/api/v1/{log.resource_type}/{log.action}",
        "status": 200,  # 默认状态码
        "request_args": {},  # 默认空对象
        "response_body": {},  # 默认空对象
        "response_time": 0.0  # 默认响应时间
    }
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="log",
        resource_id=log.id,
        details=f"查看审计日志详情：{log.details}",
        request=request
    )
    
    return Success(data=AuditLogResponse.model_validate(log_dict))

@router.delete("/delete")
async def delete_log(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除审计日志
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )
    
    log_details = log.details
    await db.delete(log)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="log",
        resource_id=id,
        details=f"删除审计日志：{log_details}",
        request=request
    )
    
    return Success(data={"message": "Log deleted successfully"}) 