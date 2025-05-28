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

@router.get("/list", summary="获取角色列表")
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    name: str = None
) -> Any:
    """
    获取角色列表
    """
    query = select(Role)
    
    # 如果不是超级管理员，只显示非超级管理员可见的角色
    if not current_user.is_superuser:
        query = query.where(Role.is_superuser_only == False)
    
    # 如果指定了租户ID，显示通用角色（非超级管理员可见且没有租户ID的角色）和该租户的角色
    if current_user.tenant_id:
        query = query.where(
            (Role.tenant_id == current_user.tenant_id) |  # 该租户的角色
            (Role.tenant_id.is_(None) & (Role.is_superuser_only == False))  # 通用角色
        )
    
    if name:
        query = query.where(Role.name.ilike(f"%{name}%"))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # 将 SQLAlchemy 模型对象转换为 Pydantic 模型对象
    role_responses = [RoleResponse.model_validate(role) for role in roles]
    
    return SuccessExtra(data=role_responses, total=total, page=page, page_size=page_size)

@router.get("/get", summary="获取角色详情")
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
    # 使用 RoleResponse 模型序列化响应
    role_response = RoleResponse.model_validate(role)
    return Success(data=role_response)

@router.post("/create", summary="创建角色")
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
        code=role_in.code,
        description=role_in.description,
        is_superuser_only=role_in.is_superuser_only,
        tenant_id=current_user.tenant_id
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    # 使用 RoleResponse 模型序列化响应
    role_response = RoleResponse.model_validate(role)
    return Success(data=role_response)


@router.post("/update", summary="更新角色")
async def update_role(
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新角色
    """
    if not role_in.id:
        raise HTTPException(
            status_code=400,
            detail="Role ID is required"
        )
        
    result = await db.execute(select(Role).where(Role.id == role_in.id))
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
    
    # 使用 RoleResponse 模型序列化响应
    role_response = RoleResponse.model_validate(role)
    return Success(data=role_response)

@router.delete("/delete", summary="删除角色")
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