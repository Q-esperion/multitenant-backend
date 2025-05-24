from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.public import UserType

class UserBase(BaseModel):
    username: str = Field(..., description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: bool = Field(True, description="是否激活")
    user_type: str = Field("tenant_user", description="用户类型")
    tenant_id: Optional[int] = Field(None, description="租户ID")
    is_tenant_admin: bool = Field(False, description="是否租户管理员")
    is_superuser: bool = Field(False, description="是否超级管理员")

class UserCreate(UserBase):
    password: str = Field(..., description="密码")
    role_ids: Optional[List[int]] = Field([], description="角色ID列表")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    user_type: Optional[str] = None
    tenant_id: Optional[int] = None
    is_tenant_admin: Optional[bool] = None
    role_ids: Optional[List[int]] = None

class UserInDBBase(UserBase):
    id: int
    tenant_id: Optional[int] = None
    is_tenant_admin: bool = False

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserInfoResponse(UserBase):
    id: int
    roles: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UpdatePasswordRequest(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")

class UserInDB(UserInDBBase):
    hashed_password: str 