from fastapi import APIRouter
from app.api.v1 import base, user, role, menu, api, tenant, log

router = APIRouter()

# 注册基础路由
router.include_router(base.router, prefix="/base", tags=["base"])

# 注册业务路由
router.include_router(user.router, prefix="/user", tags=["user"])
router.include_router(role.router, prefix="/role", tags=["role"])
router.include_router(menu.router, prefix="/menu", tags=["menu"])
router.include_router(api.router, prefix="/api", tags=["api"])
router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
router.include_router(log.router, prefix="/log", tags=["log"]) 