from datetime import datetime
from fastapi import Request
from sqlalchemy import select
from app.models.public import AuditLog
from app.db.session import AsyncSessionLocal
from app.core.log import get_logger

logger = get_logger(__name__)

async def log_audit(
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: str = None,
    request: Request = None
):
    """
    记录审计日志
    """
    try:
        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            session.add(audit_log)
            await session.commit()
            logger.debug(f"审计日志记录成功: {action} - {resource_type} - {resource_id}")
    except Exception as e:
        logger.error(f"记录审计日志失败: {str(e)}")
        # 审计日志记录失败不应该影响主业务流程
        pass 