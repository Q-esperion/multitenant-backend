from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.deps import get_current_user
from app.models.public import Api, User
from app.schemas.api import ApiCreate, ApiUpdate, ApiResponse
from app.schemas.common import Success

router = APIRouter()

@router.get("/list", response_model=Success[dict])
async def get_apis(
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
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    apis = result.scalars().all()
    
    return Success(data={
        "items": apis,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.get("/get", response_model=Success[ApiResponse])
async def get_api(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取API详情
    """
    result = await db.execute(select(Api).where(Api.id == id))
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(
            status_code=404,
            detail="API not found"
        )
    return Success(data=api)

@router.post("/create", response_model=Success[ApiResponse])
async def create_api(
    api_in: ApiCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建API
    """
    api = Api(
        **api_in.dict(),
        tenant_id=current_user.tenant_id
    )
    db.add(api)
    await db.commit()
    await db.refresh(api)
    return Success(data=api)

@router.delete("/delete", response_model=Success[dict])
async def delete_api(
    api_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除API
    """
    result = await db.execute(select(Api).where(Api.id == api_id))
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(
            status_code=404,
            detail="API not found"
        )
    
    await db.delete(api)
    await db.commit()
    return Success(data={"message": "API deleted successfully"})

@router.post("/refresh", response_model=Success[dict])
async def refresh_apis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    刷新API列表
    """
    # TODO: 实现API自动发现和更新逻辑
    return Success(data={"message": "API list refreshed successfully"}) 