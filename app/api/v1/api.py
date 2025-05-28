from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.deps import get_current_user, get_current_active_superuser
from app.db.session import get_db
from app.models.public import Api, User, TenantPermission
from app.schemas.api import ApiCreate, ApiUpdate, ApiResponse
from app.schemas.common import Success, SuccessExtra
from app.utils.audit import log_audit

router = APIRouter()

@router.get("/list")
async def get_apis(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    path: str = None,
    summary: str = None,
    tags: str = None
) -> Any:
    """
    获取API列表
    """
    query = select(Api)
    
    if path:
        query = query.where(Api.path.ilike(f"%{path}%"))
    if summary:
        query = query.where(Api.summary.ilike(f"%{summary}%"))
    if tags:
        query = query.where(Api.tags.ilike(f"%{tags}%"))
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "api",
                TenantPermission.resource_id == Api.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    apis = result.scalars().all()
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    api_list = [ApiResponse.model_validate(api) for api in apis]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="api",
        resource_id=0,
        details=f"查询API列表，筛选条件：路径={path}, 描述={summary}, 标签={tags}",
        request=request
    )
    
    return SuccessExtra(data=api_list, total=total, page=page, page_size=page_size)

@router.get("/get")
async def get_api(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取API详情
    """
    query = select(Api).where(Api.id == id)
    
    # 如果不是超级管理员，需要根据租户权限过滤
    if not current_user.is_superuser:
        query = query.join(
            TenantPermission,
            and_(
                TenantPermission.resource_type == "api",
                TenantPermission.resource_id == Api.id,
                TenantPermission.tenant_id == current_user.tenant_id
            )
        )
    
    result = await db.execute(query)
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(
            status_code=404,
            detail="API not found"
        )
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="api",
        resource_id=api.id,
        details=f"查看API详情：{api.path}",
        request=request
    )
    
    return Success(data=ApiResponse.model_validate(api))

@router.post("/create")
async def create_api(
    request: Request,
    api_in: ApiCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建API
    """
    api = Api(**api_in.model_dump())
    db.add(api)
    await db.commit()
    await db.refresh(api)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="create",
        resource_type="api",
        resource_id=api.id,
        details=f"创建新API：{api.path}",
        request=request
    )
    
    return Success(data=ApiResponse.model_validate(api))

@router.put("/update")
async def update_api(
    request: Request,
    id: int,
    api_in: ApiUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新API
    """
    result = await db.execute(select(Api).where(Api.id == id))
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(
            status_code=404,
            detail="API not found"
        )
    
    update_data = api_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api, field, value)
    
    await db.commit()
    await db.refresh(api)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="api",
        resource_id=api.id,
        details=f"更新API：{api.path}，修改字段：{', '.join(update_data.keys())}",
        request=request
    )
    
    return Success(data=ApiResponse.model_validate(api))

@router.delete("/delete")
async def delete_api(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    删除API
    """
    result = await db.execute(select(Api).where(Api.id == id))
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(
            status_code=404,
            detail="API not found"
        )
    
    api_path = api.path
    await db.delete(api)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="api",
        resource_id=id,
        details=f"删除API：{api_path}",
        request=request
    )
    
    return Success(data={"message": "API deleted successfully"})

@router.post("/refresh")
async def refresh_apis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    刷新API列表
    """
    # TODO: 实现API自动发现和更新逻辑
    return Success(data={"message": "API list refreshed successfully"}) 