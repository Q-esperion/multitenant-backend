from fastapi import APIRouter, Depends
from app.api.v1 import base, user, role, menu, api, tenant, log
from app.deps import check_permission

router = APIRouter()

# 注册基础路由
router.include_router(base.router, prefix="/base", tags=["base"])

# 注册业务路由
router.include_router(user.router, prefix="/user", tags=["user"], dependencies=[Depends(check_permission)])
router.include_router(role.router, prefix="/role", tags=["role"], dependencies=[Depends(check_permission)])
router.include_router(menu.router, prefix="/menu", tags=["menu"], dependencies=[Depends(check_permission)])
router.include_router(api.router, prefix="/api", tags=["api"], dependencies=[Depends(check_permission)])
router.include_router(tenant.router, prefix="/tenant", tags=["tenant"], dependencies=[Depends(check_permission)])
router.include_router(log.router, prefix="/log", tags=["log"], dependencies=[Depends(check_permission)]) 