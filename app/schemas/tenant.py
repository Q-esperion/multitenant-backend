from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.models.public import TenantStatus

class TenantBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: Optional[int] = 100
    expire_date: Optional[date] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(TenantBase):
    name: Optional[str] = None
    status: Optional[TenantStatus] = None

class TenantInDBBase(TenantBase):
    id: int
    schema_name: str
    status: TenantStatus
    is_deleted: bool

    class Config:
        from_attributes = True

class TenantResponse(TenantInDBBase):
    pass 