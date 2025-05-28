from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.deps import get_current_user, get_current_active_superuser
from app.db.session import get_db
from app.models.public import Menu, User, TenantPermission
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse
from app.schemas.common import Success, SuccessExtra
from app.utils.audit import log_audit

router = APIRouter()

@router.get("/list", summary="获取菜单列表")
async def get_menus(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: str = None,
    path: str = None,
    parent_id: int = None
) -> Any:
    """
    获取菜单列表
    """
    query = select(Menu)
    
    if name:
        query = query.where(Menu.name.ilike(f"%{name}%"))
    if path:
        query = query.where(Menu.path.ilike(f"%{path}%"))
    if parent_id is not None:
        query = query.where(Menu.parent_id == parent_id)
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "menu",
                TenantPermission.resource_id == Menu.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
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
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="menu",
        resource_id=0,
        details=f"查询菜单列表，筛选条件：名称={name}, 类型={parent_id}, 路径={path}",
        request=request
    )
    
    return SuccessExtra(data=menu_tree, total=total, page=page, page_size=page_size)

@router.post("/create", summary="创建菜单")
async def create_menu(
    request: Request,
    menu_in: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建菜单
    """
    menu = Menu(**menu_in.model_dump())
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="create",
        resource_type="menu",
        resource_id=menu.id,
        details=f"创建新菜单：{menu.name}",
        request=request
    )
    
    return Success(data=MenuResponse.model_validate(menu))

@router.get("/get", summary="获取菜单详情")
async def get_menu(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取菜单详情
    """
    query = select(Menu).where(Menu.id == id)
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "menu",
                TenantPermission.resource_id == Menu.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    result = await db.execute(query)
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=404,
            detail="Menu not found"
        )
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="menu",
        resource_id=menu.id,
        details=f"查看菜单详情：{menu.name}",
        request=request
    )
    
    return Success(data=MenuResponse.model_validate(menu))

@router.put("/update", summary="更新菜单")
async def update_menu(
    request: Request,
    id: int,
    menu_in: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新菜单
    """
    result = await db.execute(select(Menu).where(Menu.id == id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=404,
            detail="Menu not found"
        )
    
    update_data = menu_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(menu, field, value)
    
    await db.commit()
    await db.refresh(menu)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="menu",
        resource_id=menu.id,
        details=f"更新菜单：{menu.name}，修改字段：{', '.join(update_data.keys())}",
        request=request
    )
    
    return Success(data=MenuResponse.model_validate(menu))

@router.delete("/delete", summary="删除菜单")
async def delete_menu(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除菜单
    """
    result = await db.execute(select(Menu).where(Menu.id == id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=404,
            detail="Menu not found"
        )
    
    menu_name = menu.name
    await db.delete(menu)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="menu",
        resource_id=id,
        details=f"删除菜单：{menu.name}",
        request=request
    )
    
    return Success(data={"message": "Menu deleted successfully"}) 