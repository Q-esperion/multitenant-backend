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
    username: Optional[str] = None
    summary: Optional[str] = None
    module: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status: Optional[int] = None
    request_args: Optional[dict] = None
    response_body: Optional[dict] = None
    response_time: Optional[float] = None

    class Config:
        from_attributes = True

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