from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.deps import get_current_user, get_current_active_superuser
from app.models.public import User, AuditLog
from app.schemas.log import AuditLogResponse
from app.schemas.common import Success, SuccessExtra

router = APIRouter()

@router.get("/list")
async def get_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = None,
    action: str = None,
    start_time: str = None,
    end_time: str = None
) -> Any:
    """
    获取审计日志列表
    """
    query = select(AuditLog).where(AuditLog.is_deleted == False)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return SuccessExtra(data=logs, total=total, page=page, page_size=page_size)

@router.get("/get")
async def get_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    获取审计日志详情
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )
    return Success(data=log)

@router.delete("/delete")
async def delete_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除审计日志（软删除）
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )
    
    log.is_deleted = True
    await db.commit()
    return Success(data={"message": "Log deleted successfully"}) 