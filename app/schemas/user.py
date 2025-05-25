from datetime import datetime
from typing import Optional, List
from pydantic import EmailStr, Field, validator
from app.schemas.common import BaseSchema
import re

class RoleResponse(BaseSchema):
    id: int
    name: str

class UserBase(BaseSchema):
    username: str = Field(..., description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: bool = Field(True, description="是否激活")
    tenant_id: Optional[int] = Field(None, description="租户ID")
    is_tenant_admin: bool = Field(False, description="是否租户管理员")
    is_superuser: bool = Field(False, description="是否超级管理员")

class UserCreate(UserBase):
    password: str = Field(..., description="密码")
    role_ids: Optional[List[int]] = Field(None, description="角色ID列表")

class UserUpdate(BaseSchema):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    tenant_id: Optional[int] = None
    is_tenant_admin: Optional[bool] = None
    role_ids: Optional[List[int]] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    roles: List[dict] = []

    class Config:
        from_attributes = True

class UserInfoResponse(UserResponse):
    pass

class UpdatePasswordRequest(BaseSchema):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")

class UserInDBBase(UserBase):
    id: int
    tenant_id: Optional[int] = None
    is_tenant_admin: bool = False

class UserInDB(UserInDBBase):
    hashed_password: str

class PasswordValidator(BaseSchema):
    password: str = Field(..., description="密码")

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度不能小于8位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("密码必须包含特殊字符")
        return v

class ResetPasswordRequest(BaseSchema):
    new_password: Optional[str] = Field(None, description="新密码")

    @validator("new_password")
    def validate_password(cls, v):
        if v is not None:
            return PasswordValidator(password=v).password
        return v 