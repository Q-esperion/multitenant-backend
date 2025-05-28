from typing import Optional
from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    is_superuser_only: bool = False
    tenant_id: Optional[int] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    is_superuser_only: Optional[bool] = None
    tenant_id: Optional[int] = None

class RoleInDBBase(RoleBase):
    id: int

    class Config:
        from_attributes = True

class RoleResponse(RoleInDBBase):
    pass 