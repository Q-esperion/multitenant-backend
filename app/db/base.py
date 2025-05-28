# 导入所有模型，以便Alembic可以检测到它们
from app.db.base_class import Base
from app.models.public import (
    User,
    Role,
    Menu,
    Api,
    Tenant,
    TenantPermission,
    AuditLog,
    AccessLog,
    RoleMenu,
    RoleApi,
    UserRole
)

# 导出所有模型
__all__ = [
    "Base",
    "User",
    "Role",
    "Menu",
    "Api",
    "Tenant",
    "TenantPermission",
    "AuditLog",
    "AccessLog",
    "RoleMenu",
    "RoleApi",
    "UserRole"
] 