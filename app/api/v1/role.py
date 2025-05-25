from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.deps import get_current_user
from app.models.public import Role, User, UserRole
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.common import Success, SuccessExtra

router = APIRouter()

@router.get("/list")
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: str = None
) -> Any:
    """
    获取角色列表
    """
    query = select(Role).where(Role.tenant_id == current_user.tenant_id)
    if name:
        query = query.where(Role.name.ilike(f"%{name}%"))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    roles = result.scalars().all()
    
    return SuccessExtra(data=roles, total=total, page=page, page_size=page_size)

@router.get("/get")
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取角色详情
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    return Success(data=role)

@router.post("/create")
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建角色
    """
    role = Role(
        name=role_in.name,
        description=role_in.description,
        tenant_id=current_user.tenant_id
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return Success(data=role)

@router.put("/update")
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新角色
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    update_data = role_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    await db.commit()
    await db.refresh(role)
    return Success(data=role)

@router.delete("/delete")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除角色
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    await db.delete(role)
    await db.commit()
    return Success(data={"message": "Role deleted successfully"}) 