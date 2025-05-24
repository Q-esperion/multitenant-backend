from typing import Optional
from pydantic import BaseModel
from app.models.public import MethodType

class ApiBase(BaseModel):
    path: str
    method: MethodType
    summary: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None

class ApiCreate(ApiBase):
    pass

class ApiUpdate(ApiBase):
    path: Optional[str] = None
    method: Optional[MethodType] = None

class ApiInDBBase(ApiBase):
    id: int
    tenant_id: Optional[int] = None

    class Config:
        from_attributes = True

class ApiResponse(ApiInDBBase):
    pass 