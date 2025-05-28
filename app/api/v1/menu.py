from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.deps import get_current_user
from app.db.session import get_db
from app.models.public import Menu, User, TenantPermission
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse
from app.schemas.common import Success, SuccessExtra

router = APIRouter()

@router.get("/list", summary="获取菜单列表")
async def get_menus(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    获取菜单列表
    """
    # 如果是超级管理员，可以查看所有菜单
    if current_user.is_superuser:
        query = select(Menu).where(Menu.is_deleted == False)
    else:
        # 否则只能查看租户有权限的菜单
        query = (
            select(Menu)
            .join(TenantPermission, Menu.id == TenantPermission.menu_id)
            .where(
                and_(
                    TenantPermission.tenant_id == current_user.tenant_id,
                    TenantPermission.is_enabled == True,
                    Menu.is_deleted == False
                )
            )
        )
    
    query = query.order_by(Menu.order).offset(skip).limit(limit)
    result = await db.execute(query)
    menus = result.scalars().all()
    
    # 将 SQLAlchemy 模型转换为字典，并添加 title 字段
    menu_dicts = []
    for menu in menus:
        menu_dict = {
            "id": menu.id,
            "name": menu.name,
            "title": menu.name,  # 使用 name 作为 title
            "menu_type": menu.menu_type,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "is_hidden": menu.is_hidden,
            "keepalive": menu.keepalive,
            "redirect": menu.redirect,
            "is_enabled": menu.is_enabled,
            "children": []  # 初始化为空列表
        }
        menu_dicts.append(menu_dict)
    
    # 构建树形结构
    menu_tree = []
    menu_map = {menu["id"]: menu for menu in menu_dicts}
    
    for menu in menu_dicts:
        if menu["parent_id"] is None:
            menu_tree.append(menu)
        else:
            parent = menu_map.get(menu["parent_id"])
            if parent:
                parent["children"].append(menu)
    
    return SuccessExtra(data=menu_tree, total=len(menu_tree), page=1, page_size=limit)

@router.post("/create", summary="创建菜单")
async def create_menu(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    menu_in: MenuCreate
) -> Any:
    """
    创建新菜单
    """
    # 只有超级管理员可以创建菜单
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建菜单"
        )
    
    # 如果 component 为空，使用默认值 "Layout"
    menu_data = menu_in.model_dump()
    if not menu_data.get("component"):
        menu_data["component"] = "Layout"
    
    # 如果 parent_id 为 0，设置为 None
    if menu_data.get("parent_id") == 0:
        menu_data["parent_id"] = None
    
    menu = Menu(**menu_data)
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    
    # 转换为字典并添加 title 字段
    menu_dict = {
        "id": menu.id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "path": menu.path,
        "component": menu.component,
        "icon": menu.icon,
        "order": menu.order,
        "parent_id": menu.parent_id,
        "is_hidden": menu.is_hidden,
        "keepalive": menu.keepalive,
        "redirect": menu.redirect,
        "is_enabled": menu.is_enabled,
        "children": []
    }
    return Success(data=menu_dict)

@router.get("/get", summary="获取菜单详情")
async def get_menu(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int
) -> Any:
    """
    获取指定菜单
    """
    # 如果是超级管理员，可以查看所有菜单
    if current_user.is_superuser:
        query = select(Menu).where(Menu.id == id, Menu.is_deleted == False)
    else:
        # 否则只能查看租户有权限的菜单
        query = (
            select(Menu)
            .join(TenantPermission, Menu.id == TenantPermission.menu_id)
            .where(
                and_(
                    Menu.id == id,
                    TenantPermission.tenant_id == current_user.tenant_id,
                    TenantPermission.is_enabled == True,
                    Menu.is_deleted == False
                )
            )
        )
    
    result = await db.execute(query)
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    # 转换为字典并添加 title 字段
    menu_dict = {
        "id": menu.id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "path": menu.path,
        "component": menu.component,
        "icon": menu.icon,
        "order": menu.order,
        "parent_id": menu.parent_id,
        "is_hidden": menu.is_hidden,
        "keepalive": menu.keepalive,
        "redirect": menu.redirect,
        "is_enabled": menu.is_enabled,
        "children": []
    }
    return Success(data=menu_dict)

@router.put("/update", summary="更新菜单")
async def update_menu(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
    menu_in: MenuUpdate
) -> Any:
    """
    更新菜单
    """
    # 只有超级管理员可以更新菜单
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以更新菜单"
        )
    
    result = await db.execute(
        select(Menu)
        .where(Menu.id == id)
        .where(Menu.is_deleted == False)
    )
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    for field, value in menu_in.model_dump(exclude_unset=True).items():
        setattr(menu, field, value)
    
    await db.commit()
    await db.refresh(menu)
    
    # 转换为字典并添加 title 字段
    menu_dict = {
        "id": menu.id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "path": menu.path,
        "component": menu.component,
        "icon": menu.icon,
        "order": menu.order,
        "parent_id": menu.parent_id,
        "is_hidden": menu.is_hidden,
        "keepalive": menu.keepalive,
        "redirect": menu.redirect,
        "is_enabled": menu.is_enabled,
        "children": []
    }
    return Success(data=menu_dict)

@router.delete("/delete", summary="删除菜单")
async def delete_menu(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int
) -> Any:
    """
    删除菜单
    """
    # 只有超级管理员可以删除菜单
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除菜单"
        )
    
    result = await db.execute(
        select(Menu)
        .where(Menu.id == id)
        .where(Menu.is_deleted == False)
    )
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    menu.is_deleted = True
    await db.commit()
    await db.refresh(menu)
    
    # 转换为字典并添加 title 字段
    menu_dict = {
        "id": menu.id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "path": menu.path,
        "component": menu.component,
        "icon": menu.icon,
        "order": menu.order,
        "parent_id": menu.parent_id,
        "is_hidden": menu.is_hidden,
        "keepalive": menu.keepalive,
        "redirect": menu.redirect,
        "is_enabled": menu.is_enabled,
        "children": []
    }
    return Success(data=menu_dict) 