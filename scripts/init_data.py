"""
初始化数据脚本
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.public import User, Role, Menu, Api, Tenant
from app.core.security import get_password_hash
from app.core.log import get_logger

logger = get_logger(__name__)

async def init_data():
    """初始化基础数据"""
    try:
        async with AsyncSessionLocal() as session:
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
            menus = [
                Menu(
                    name="系统管理",
                    menu_type="catalog",
                    path="/system",
                    component="Layout",
                    icon="system",
                    order=1
                ),
                Menu(
                    name="用户管理",
                    menu_type="menu",
                    path="/system/user",
                    component="system/user/index",
                    icon="user",
                    order=1,
                    parent_id=1
                ),
                Menu(
                    name="角色管理",
                    menu_type="menu",
                    path="/system/role",
                    component="system/role/index",
                    icon="role",
                    order=2,
                    parent_id=1
                )
            ]
            for menu in menus:
                session.add(menu)
            await session.flush()
            
            # 创建API
            apis = [
                Api(
                    path="/api/v1/user/list",
                    method="GET",
                    summary="获取用户列表",
                    tags="用户管理"
                ),
                Api(
                    path="/api/v1/user/create",
                    method="POST",
                    summary="创建用户",
                    tags="用户管理"
                ),
                Api(
                    path="/api/v1/role/list",
                    method="GET",
                    summary="获取角色列表",
                    tags="角色管理"
                )
            ]
            for api in apis:
                session.add(api)
            
            await session.commit()
            logger.info("基础数据初始化完成")
    except Exception as e:
        await session.rollback()
        logger.error(f"基础数据初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_data()) 