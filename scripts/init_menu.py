"""
初始化数据脚本
"""

import asyncio
import sys
import os
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
            # await session.execute(delete(AuditLog))    # 新增
            # await session.execute(delete(AccessLog))   # 新增
            # await session.execute(delete(RoleApi))
            await session.execute(delete(RoleMenu))
            # await session.execute(delete(TenantPermission))
            # await session.execute(delete(UserRole))
            # await session.execute(delete(Api))
            await session.execute(delete(Menu))
            # await session.execute(delete(Role))
            # await session.execute(delete(User))
            # await session.execute(delete(Tenant))
            await session.commit()
            logger.info("原始菜单数据清除完成")
            
            
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
            
            logger.info("菜单数据全量更新完成")
    except Exception as e:
        await session.rollback()
        logger.error(f"基础数据初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_data()) 