"""
初始化数据脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# 在设置路径之后再导入其他模块
from datetime import datetime
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.models.public import User, Role, Menu, Api, Tenant, RoleApi, RoleMenu, TenantPermission, UserRole, AuditLog, AccessLog
from app.core.security import get_password_hash
from app.core.log import get_logger
from app.utils.router_parser import generate_menu_from_router, generate_api_from_router
from app.api.v1.router import router as api_v1_router

logger = get_logger(__name__)

async def init_data():
    """初始化基础数据"""
    try:
        async with AsyncSessionLocal() as session:
            # 清除所有数据
            logger.info("开始清除所有数据...")
            await session.execute(delete(AuditLog))    # 新增
            await session.execute(delete(AccessLog))   # 新增
            await session.execute(delete(RoleApi))
            await session.execute(delete(RoleMenu))
            await session.execute(delete(TenantPermission))
            await session.execute(delete(UserRole))
            await session.execute(delete(Api))
            await session.execute(delete(Menu))
            # await session.execute(delete(Role))
            # await session.execute(delete(User))
            # await session.execute(delete(Tenant))
            await session.commit()
            logger.info("数据清除完成")
            
            # 创建超级管理员
            superuser = User(
                username="admin",
                password=get_password_hash("Admin@123456"),
                email="admin@example.com",
                is_active=True,
                is_superuser=True,
                is_tenant_admin=False
            )
            session.add(superuser)
            await session.flush()
            
            # 创建角色
            roles = [
                Role(
                    name="超级管理员",
                    code="super_admin",
                    description="系统超级管理员"
                ),
                Role(
                    name="租户管理员",
                    code="tenant_admin",
                    description="租户管理员"
                ),
                Role(
                    name="普通用户",
                    code="normal_user",
                    description="普通用户"
                )
            ]
            for role in roles:
                session.add(role)
            await session.flush()
            
           # 创建菜单
            # 检查是否已存在菜单
            result = await session.execute(select(Menu))
            existing_menus = result.scalars().all()

            if not existing_menus:
                # 创建系统管理父菜单
                system_menu = Menu(
                    menu_type="catalog",
                    name="系统管理",
                    path="/system",
                    order=1,
                    parent_id=None,
                    icon="carbon:gui-management",
                    is_hidden=False,
                    component="Layout",
                    keepalive=False,
                    redirect="/system/user"
                )
                session.add(system_menu)
                await session.flush()  # 获取 system_menu.id

                # 创建系统管理子菜单
                system_children = [
                    Menu(
                        menu_type="menu",
                        name="用户管理",
                        path="user",
                        order=1,
                        parent_id=system_menu.id,
                        icon="material-symbols:person-outline-rounded",
                        is_hidden=False,
                        component="/system/user",
                        keepalive=False
                    ),
                    Menu(
                        menu_type="menu",
                        name="角色管理",
                        path="role",
                        order=2,
                        parent_id=system_menu.id,
                        icon="carbon:user-role",
                        is_hidden=False,
                        component="/system/role",
                        keepalive=False
                    ),
                    Menu(
                        menu_type="menu",
                        name="菜单管理",
                        path="menu",
                        order=3,
                        parent_id=system_menu.id,
                        icon="material-symbols:list-alt-outline",
                        is_hidden=False,
                        component="/system/menu",
                        keepalive=False
                    ),
                    Menu(
                        menu_type="menu",
                        name="API管理",
                        path="api",
                        order=4,
                        parent_id=system_menu.id,
                        icon="ant-design:api-outlined",
                        is_hidden=False,
                        component="/system/api",
                        keepalive=False
                    ),
                    Menu(
                        menu_type="menu",
                        name="部门管理",
                        path="dept",
                        order=5,
                        parent_id=system_menu.id,
                        icon="mingcute:department-line",
                        is_hidden=False,
                        component="/system/dept",
                        keepalive=False
                    ),
                    Menu(
                        menu_type="menu",
                        name="审计日志",
                        path="auditlog",
                        order=6,
                        parent_id=system_menu.id,
                        icon="ph:clipboard-text-bold",
                        is_hidden=False,
                        component="/system/auditlog",
                        keepalive=False
                    ),
                ]
                for menu in system_children:
                    session.add(menu)

                # 创建一级菜单
                top_menu = Menu(
                    menu_type="menu",
                    name="一级菜单",
                    path="/top-menu",
                    order=2,
                    parent_id=None,
                    icon="material-symbols:featured-play-list-outline",
                    is_hidden=False,
                    component="/top-menu",
                    keepalive=False,
                    redirect=""
                )
                session.add(top_menu)
            
            # 创建API
            # 获取所有API路由
            apis = generate_api_from_router(api_v1_router)
            
            # 创建API记录
            for api_data in apis:
                api = Api(
                    path=api_data["path"],
                    method=api_data["method"],
                    summary=api_data["summary"],
                    tags=api_data["tags"],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(api)
            
            await session.commit()
            logger.info("基础数据初始化完成")
    except Exception as e:
        await session.rollback()
        logger.error(f"基础数据初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_data()) 