from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.public import AuditLog
from app.db.session import async_session

async def log_audit(
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: Optional[str] = None,
    request: Optional[Request] = None
) -> None:
    """
    记录审计日志
    
    Args:
        user_id: 用户ID
        action: 操作类型（如：create, update, delete等）
        resource_type: 资源类型（如：user, role, menu等）
        resource_id: 资源ID
        details: 详细信息
        request: FastAPI请求对象，用于获取IP地址和User-Agent
    """
    async with async_session() as session:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        session.add(audit_log)
        await session.commit() 