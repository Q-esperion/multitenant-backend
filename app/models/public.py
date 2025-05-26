from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, DateTime, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
import enum
from .base import BaseModel, Base
from datetime import datetime
import pytz

def get_current_time():
    """获取当前时区的时间"""
    return datetime.now(pytz.timezone('Asia/Shanghai'))

class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class MethodType(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class MenuType(str, enum.Enum):
    CATALOG = "catalog"  # 目录
    MENU = "menu"       # 菜单
    BUTTON = "button"   # 按钮

class Tenant(BaseModel):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True, comment="租户ID")
    name = Column(String(100), nullable=False, comment="租户名称")
    schema_name = Column(String(100), nullable=False, unique=True, comment="Schema名称")
    status = Column(String(20), default=TenantStatus.ACTIVE.value, comment="租户状态")
    description = Column(String(500), comment="租户描述")
    max_users = Column(Integer, default=100, comment="最大用户数")
    expire_date = Column(Date, comment="到期时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    users = relationship("User", back_populates="tenant")
    permissions = relationship("TenantPermission", back_populates="tenant")

class User(BaseModel):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    alias = Column(String(50), nullable=True, comment="用户别名")
    email = Column(String(100), unique=True, index=True, nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    password = Column(String(100), nullable=False, comment="密码")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    last_login = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    department = Column(String(100), nullable=True, comment="部门名称")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    is_tenant_admin = Column(Boolean, default=False, comment="是否租户管理员")
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'), nullable=False, comment="更新时间")
    
    # 关系
    tenant = relationship("Tenant", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    access_logs = relationship("AccessLog", back_populates="user")
    roles = relationship("Role", secondary="user_roles", back_populates="users")

class Role(BaseModel):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, unique=True, comment="角色编码")
    description = Column(String(200), comment="角色描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    role_menus = relationship("RoleMenu", back_populates="role")
    role_apis = relationship("RoleApi", back_populates="role")
    users = relationship("User", secondary="user_roles", back_populates="roles")

class Api(BaseModel):
    __tablename__ = "apis"
    
    id = Column(Integer, primary_key=True, index=True, comment="API ID")
    path = Column(String(200), nullable=False, comment="API路径")
    method = Column(String(10), nullable=False, comment="请求方法")
    summary = Column(String(200), comment="接口摘要")
    tags = Column(String(100), comment="标签")
    description = Column(String(500), comment="接口描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 关系
    permissions = relationship("TenantPermission", back_populates="api")
    role_apis = relationship("RoleApi", back_populates="api")

class Menu(BaseModel):
    __tablename__ = "menus"
    
    id = Column(Integer, primary_key=True, index=True, comment="菜单ID")
    name = Column(String(50), nullable=False, comment="菜单名称")
    menu_type = Column(String(20), nullable=False, comment="菜单类型")
    path = Column(String(100), nullable=False, comment="菜单路径")
    component = Column(String(100), nullable=False, comment="组件路径")
    icon = Column(String(50), nullable=True, comment="图标")
    order = Column(Integer, default=0, comment="排序")
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True, comment="父菜单ID")
    is_hidden = Column(Boolean, default=False, comment="是否隐藏")
    keepalive = Column(Boolean, default=False, comment="是否缓存")
    redirect = Column(String(200), nullable=True, comment="重定向")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")

    # 关系
    parent = relationship("Menu", remote_side=[id], backref="children")
    role_menus = relationship("RoleMenu", back_populates="menu")
    permissions = relationship("TenantPermission", back_populates="menu")

class TenantPermission(BaseModel):
    __tablename__ = "tenant_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=True)
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # 关系
    tenant = relationship("Tenant", back_populates="permissions")
    menu = relationship("Menu", back_populates="permissions")
    api = relationship("Api", back_populates="permissions")

    __table_args__ = (
        CheckConstraint(
            "(menu_id IS NOT NULL AND api_id IS NULL) OR (menu_id IS NULL AND api_id IS NOT NULL)",
            name="check_menu_or_api"
        ),
    )

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=False)
    details = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="audit_logs")

class AccessLog(BaseModel):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    path = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Integer)  # 响应时间（毫秒）
    process_time = Column(Integer)  # 处理时间（毫秒）
    ip_address = Column(String(50))
    user_agent = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    
    user = relationship("User", back_populates="access_logs")

class RoleMenu(Base):
    __tablename__ = "role_menus"
    
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, primary_key=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False, primary_key=True)
    
    role = relationship("Role", back_populates="role_menus")
    menu = relationship("Menu", back_populates="role_menus")

class RoleApi(Base):
    """角色-API关系表"""
    __tablename__ = "role_apis"
    
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, primary_key=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False, primary_key=True)
    
    # 关系
    role = relationship("Role", back_populates="role_apis")
    api = relationship("Api", back_populates="role_apis")

class UserRole(Base):
    """用户-角色关系表"""
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, primary_key=True) 