from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.public import UserType

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    user_type: Optional[UserType] = UserType.NORMAL_USER

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    tenant_id: Optional[int] = None
    is_tenant_admin: bool = False

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    alias: Optional[str] = None
    phone: Optional[str] = None
    dept_id: Optional[int] = None
    tenant_id: Optional[int] = None
    is_tenant_admin: bool = False
    last_login: Optional[str] = None

    class Config:
        from_attributes = True

class UserInfoResponse(UserResponse):
    roles: List[str] = []

class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserInDB(UserInDBBase):
    hashed_password: str 