from typing import Optional
from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    name: Optional[str] = None

class RoleInDBBase(RoleBase):
    id: int
    tenant_id: Optional[int] = None

    class Config:
        from_attributes = True

class RoleResponse(RoleInDBBase):
    pass 