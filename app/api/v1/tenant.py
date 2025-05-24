from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db.session import get_db
from app.deps import get_current_user, get_current_active_superuser
from app.models.public import Tenant, User, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.schemas.common import Success

router = APIRouter()

@router.get("/list", response_model=Success[dict])
async def get_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
) -> Any:
    """
    获取租户列表
    """
    query = select(Tenant).where(Tenant.is_deleted == False)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    
    return Success(data={
        "items": tenants,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.post("/create", response_model=Success[TenantResponse])
async def create_tenant(
    tenant_in: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建租户
    """
    # 创建租户记录
    tenant = Tenant(
        name=tenant_in.name,
        schema_name=f"tenant_{tenant_in.name.lower().replace(' ', '_')}",
        status=TenantStatus.ACTIVE,
        description=tenant_in.description,
        max_users=tenant_in.max_users,
        expire_date=tenant_in.expire_date
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    # 创建租户schema
    schema_name = tenant.schema_name
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    
    return Success(data=tenant)

@router.put("/update", response_model=Success[TenantResponse])
async def update_tenant(
    tenant_id: int,
    tenant_in: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新租户信息
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    update_data = tenant_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    await db.commit()
    await db.refresh(tenant)
    return Success(data=tenant)

@router.delete("/delete", response_model=Success[dict])
async def delete_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除租户（软删除）
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    tenant.is_deleted = True
    await db.commit()
    return Success(data={"message": "Tenant deleted successfully"}) 