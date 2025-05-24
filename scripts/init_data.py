import asyncio
import sys
import os
from pathlib import Path
import inspect
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.db.session import async_session
from app.models.public import (
    User, Role, Menu, Api, Tenant, TenantPermission, 
    MenuType, MethodType, RoleMenu, RoleApi
)
from app.core.security import get_password_hash
from app.core.config import settings
from app.api.v1 import api as api_controller
from app.api.v1 import base, user, role, menu, api, tenant, log
from sqlalchemy import select
from fastapi import APIRouter

async def get_all_apis() -> List[Dict[str, Any]]:
    """获取所有API路由信息"""
    apis = []
    
    # 获取所有路由模块
    modules = [base, user, role, menu, api, tenant, log]
    
    for module in modules:
        if hasattr(module, "router"):
            router = module.router
            # 获取路由的所有端点
            for route in router.routes:
                if hasattr(route, "methods") and hasattr(route, "path"):
                    # 获取API的详细信息
                    path = route.path
                    methods = route.methods
                    summary = route.summary if hasattr(route, "summary") else ""
                    tags = route.tags if hasattr(route, "tags") else []
                    description = route.description if hasattr(route, "description") else ""
                    
                    # 为每个HTTP方法创建一个API记录
                    for method in methods:
                        if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                            apis.append({
                                "path": path,
                                "method": method,
                                "summary": summary,
                                "tags": ",".join(tags) if tags else "",
                                "description": description
                            })
    
    return apis

async def init_tenant():
    """初始化租户数据"""
    async with async_session() as session:
        # 检查是否已存在默认租户
        tenant = await session.get(Tenant, 1)
        if not tenant:
            tenant = Tenant(
                id=1,
                name="默认租户",
                schema_name="default",
                description="系统默认租户",
                status="active"
            )
            session.add(tenant)
            await session.commit()
            print("租户数据初始化完成")
        else:
            print("租户数据已存在")

async def init_users():
    """初始化用户数据"""
    async with async_session() as session:
        # 检查是否已存在超级管理员
        admin = await session.get(User, 1)
        if not admin:
            # 创建超级管理员
            admin = User(
                id=1,
                username="admin",
                password=get_password_hash("123456"),
                email="admin@example.com",
                is_active=True,
                is_superuser=True,
                user_type="super_admin"
            )
            session.add(admin)
            await session.commit()
            print("超级管理员初始化完成")
        else:
            print("超级管理员已存在")

async def init_roles():
    """初始化角色数据"""
    async with async_session() as session:
        # 检查是否已存在默认角色
        roles = [
            {
                "id": 1,
                "name": "系统管理员",
                "code": "admin",
                "description": "系统管理员角色"
            },
            {
                "id": 2,
                "name": "租户管理员",
                "code": "tenant_admin",
                "description": "租户管理员角色"
            },
            {
                "id": 3,
                "name": "普通用户",
                "code": "user",
                "description": "普通用户角色"
            }
        ]
        
        for role_data in roles:
            role = await session.get(Role, role_data["id"])
            if not role:
                role = Role(**role_data)
                session.add(role)
        
        await session.commit()
        print("角色数据初始化完成")

async def init_menus():
    """初始化菜单数据"""
    async with async_session() as session:
        # 检查是否已存在默认菜单
        menus = [
            {
                "id": 1,
                "name": "系统管理",
                "path": "/system",
                "component": "Layout",
                "icon": "carbon:gui-management",
                "order": 1,
                "parent_id": None,
                "menu_type": "catalog",
                "is_hidden": False,
                "keepalive": False,
                "redirect": "/system/user"
            },
            {
                "id": 2,
                "name": "用户管理",
                "path": "user",
                "component": "/system/user",
                "icon": "material-symbols:person-outline-rounded",
                "order": 1,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            },
            {
                "id": 3,
                "name": "角色管理",
                "path": "role",
                "component": "/system/role",
                "icon": "carbon:user-role",
                "order": 2,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            },
            {
                "id": 4,
                "name": "菜单管理",
                "path": "menu",
                "component": "/system/menu",
                "icon": "material-symbols:list-alt-outline",
                "order": 3,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            },
            {
                "id": 5,
                "name": "API管理",
                "path": "api",
                "component": "/system/api",
                "icon": "ant-design:api-outlined",
                "order": 4,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            },
            {
                "id": 6,
                "name": "部门管理",
                "path": "dept",
                "component": "/system/dept",
                "icon": "mingcute:department-line",
                "order": 5,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            },
            {
                "id": 7,
                "name": "审计日志",
                "path": "auditlog",
                "component": "/system/auditlog",
                "icon": "ph:clipboard-text-bold",
                "order": 6,
                "parent_id": 1,
                "menu_type": "menu",
                "is_hidden": False,
                "keepalive": False
            }
        ]
        
        for menu_data in menus:
            menu = await session.get(Menu, menu_data["id"])
            if not menu:
                menu = Menu(**menu_data)
                session.add(menu)
        
        await session.commit()
        print("菜单数据初始化完成")

async def init_apis():
    """初始化API数据"""
    async with async_session() as session:
        # 获取所有API路由信息
        apis = await get_all_apis()
        
        # 检查是否已存在API数据
        result = await session.execute(select(Api))
        existing_apis = result.scalars().all()
        
        if not existing_apis:
            # 创建新的API记录
            for api_data in apis:
                api = Api(**api_data)
                session.add(api)
            await session.commit()
            print(f"API数据初始化完成，共添加 {len(apis)} 个API")
        else:
            # 更新现有API记录
            for api_data in apis:
                # 查找匹配的API
                existing_api = next(
                    (api for api in existing_apis if api.path == api_data["path"] and api.method == api_data["method"]),
                    None
                )
                
                if existing_api:
                    # 更新现有API
                    existing_api.summary = api_data["summary"]
                    existing_api.tags = api_data["tags"]
                    existing_api.description = api_data["description"]
                else:
                    # 添加新API
                    api = Api(**api_data)
                    session.add(api)
            
            await session.commit()
            print(f"API数据更新完成，共处理 {len(apis)} 个API")

async def init_role_permissions():
    """初始化角色权限数据"""
    async with async_session() as session:
        # 获取所有角色
        result = await session.execute(select(Role))
        roles = result.scalars().all()
        
        # 获取所有菜单和API
        result = await session.execute(select(Menu))
        menus = result.scalars().all()
        result = await session.execute(select(Api))
        apis = result.scalars().all()
        
        for role in roles:
            # 检查是否已存在角色-菜单关系
            result = await session.execute(
                select(RoleMenu).where(RoleMenu.role_id == role.id)
            )
            existing_role_menus = result.scalars().all()
            existing_menu_ids = {rm.menu_id for rm in existing_role_menus}
            
            # 检查是否已存在角色-API关系
            result = await session.execute(
                select(RoleApi).where(RoleApi.role_id == role.id)
            )
            existing_role_apis = result.scalars().all()
            existing_api_ids = {ra.api_id for ra in existing_role_apis}
            
            # 根据角色类型分配权限
            if role.code == "admin":
                # 系统管理员拥有所有权限
                for menu in menus:
                    if menu.id not in existing_menu_ids:
                        role_menu = RoleMenu(role_id=role.id, menu_id=menu.id)
                        session.add(role_menu)
                
                for api in apis:
                    if api.id not in existing_api_ids:
                        role_api = RoleApi(role_id=role.id, api_id=api.id)
                        session.add(role_api)
            
            elif role.code == "tenant_admin":
                # 租户管理员拥有除系统管理外的所有权限
                for menu in menus:
                    if menu.id not in existing_menu_ids and menu.parent_id != 1:
                        role_menu = RoleMenu(role_id=role.id, menu_id=menu.id)
                        session.add(role_menu)
                
                for api in apis:
                    if api.id not in existing_api_ids and not api.path.startswith("/system"):
                        role_api = RoleApi(role_id=role.id, api_id=api.id)
                        session.add(role_api)
            
            else:
                # 普通用户只有基本权限
                basic_menu_ids = [2, 6]  # 用户管理和部门管理
                for menu in menus:
                    if menu.id not in existing_menu_ids and menu.id in basic_menu_ids:
                        role_menu = RoleMenu(role_id=role.id, menu_id=menu.id)
                        session.add(role_menu)
                
                # 只给基本API权限
                basic_api_paths = ["/user/profile", "/dept/list"]
                for api in apis:
                    if api.id not in existing_api_ids and api.path in basic_api_paths:
                        role_api = RoleApi(role_id=role.id, api_id=api.id)
                        session.add(role_api)
        
        await session.commit()
        print("角色权限数据初始化完成")

async def init_all():
    """初始化所有数据"""
    await init_tenant()
    await init_users()
    await init_roles()
    await init_menus()
    await init_apis()
    await init_role_permissions()
    print("所有数据初始化完成")

if __name__ == "__main__":
    asyncio.run(init_all()) 