from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.deps import get_current_user
from app.db.session import get_db
from app.models.public import Menu, User
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
    result = await db.execute(
        select(Menu)
        .where(Menu.tenant_id == current_user.tenant_id)
        .where(Menu.is_deleted == False)
        .order_by(Menu.order)
        .offset(skip)
        .limit(limit)
    )
    menus = result.scalars().all()
    return SuccessExtra(data=menus, total=len(menus), page=1, page_size=limit)

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
    menu = Menu(**menu_in.model_dump())
    menu.tenant_id = current_user.tenant_id
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return Success(data=menu)

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
    result = await db.execute(
        select(Menu)
        .where(Menu.id == id)
        .where(Menu.tenant_id == current_user.tenant_id)
        .where(Menu.is_deleted == False)
    )
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    return Success(data=menu)

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
    result = await db.execute(
        select(Menu)
        .where(Menu.id == id)
        .where(Menu.tenant_id == current_user.tenant_id)
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
    return Success(data=menu)

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
    result = await db.execute(
        select(Menu)
        .where(Menu.id == id)
        .where(Menu.tenant_id == current_user.tenant_id)
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
    return Success(data=menu) 