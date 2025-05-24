from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AuditLogBase(BaseModel):
    user_id: int
    action: str
    resource_type: str
    resource_id: int
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogInDBBase(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(AuditLogInDBBase):
    pass

class AccessLogBase(BaseModel):
    user_id: int
    path: str
    method: str
    status_code: int
    response_time: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AccessLogCreate(AccessLogBase):
    pass

class AccessLogInDBBase(AccessLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AccessLogResponse(AccessLogInDBBase):
    pass 