from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.deps import get_current_user, get_current_active_superuser
from app.db.session import get_db
from app.models.public import Role, User, TenantPermission
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.common import Success, SuccessExtra
from app.utils.audit import log_audit

router = APIRouter()

@router.get("/list", summary="获取角色列表")
async def get_roles(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    role_name: str = None,
    code: str = None
) -> Any:
    """
    获取角色列表
    """
    query = select(Role)
    
    if role_name:
        query = query.where(Role.name.ilike(f"%{role_name}%"))
    if code:
        query = query.where(Role.code.ilike(f"%{code}%"))
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "role",
                TenantPermission.resource_id == Role.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    role_list = [RoleResponse.model_validate(role) for role in roles]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="role",
        resource_id=0,
        details=f"查询角色列表，筛选条件：角色名称={role_name}, 角色编码={code}",
        request=request
    )
    
    return SuccessExtra(data=role_list, total=total, page=page, page_size=page_size)

@router.get("/get", summary="获取角色详情")
async def get_role(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取角色详情
    """
    query = select(Role).where(Role.id == id)
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "role",
                TenantPermission.resource_id == Role.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    result = await db.execute(query)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="role",
        resource_id=role.id,
        details=f"查看角色详情：{role.name}",
        request=request
    )
    
    return Success(data=RoleResponse.model_validate(role))

@router.post("/create", summary="创建角色")
async def create_role(
    request: Request,
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建角色
    """
    role = Role(**role_in.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="create",
        resource_type="role",
        resource_id=role.id,
        details=f"创建新角色：{role.name}",
        request=request
    )
    
    return Success(data=RoleResponse.model_validate(role))

@router.post("/update", summary="更新角色")
async def update_role(
    request: Request,
    id: int,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新角色
    """
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    await db.commit()
    await db.refresh(role)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="role",
        resource_id=role.id,
        details=f"更新角色：{role.name}，修改字段：{', '.join(update_data.keys())}",
        request=request
    )
    
    return Success(data=RoleResponse.model_validate(role))

@router.delete("/delete", summary="删除角色")
async def delete_role(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除角色
    """
    result = await db.execute(select(Role).where(Role.id == id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    role_name = role.name
    await db.delete(role)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="role",
        resource_id=id,
        details=f"删除角色：{role_name}",
        request=request
    )
    
    return Success(data={"message": "Role deleted successfully"}) 