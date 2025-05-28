from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db.session import get_db
from app.deps import get_current_user, get_current_active_superuser
from app.models.public import Tenant, User, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.schemas.common import Success, SuccessExtra
from app.core.log import get_logger
from app.utils.audit import log_audit
from datetime import date
from app.core.tenant_tables import init_tenant_schema

router = APIRouter()
logger = get_logger(__name__)

@router.get("/list")
async def get_tenants(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: str = None,
    status: str = None
) -> Any:
    """
    获取租户列表
    """
    logger.debug(f"开始获取租户列表，页码: {page}, 每页数量: {page_size}, 搜索参数: name={name}, status={status}")
    query = select(Tenant).where(Tenant.is_deleted == False)
    
    # 添加搜索条件
    if name:
        query = query.where(Tenant.name.ilike(f"%{name}%"))
    if status:
        query = query.where(Tenant.status == status)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    logger.debug(f"查询到 {len(tenants)} 个租户")
    
    # 将 SQLAlchemy 对象转换为 Pydantic 模型
    tenant_list = [TenantResponse.model_validate(tenant) for tenant in tenants]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="tenant",
        resource_id=0,
        details=f"查询租户列表，页码：{page}，每页数量：{page_size}，搜索条件：name={name}, status={status}",
        request=request
    )
    
    return SuccessExtra(data=tenant_list, total=total, page=page, page_size=page_size)

@router.post("/create")
async def create_tenant(
    request: Request,
    tenant_in: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建租户
    """
    try:
        logger.info(f"开始创建租户: {tenant_in.name}")
        logger.debug(f"租户创建参数: {tenant_in.model_dump()}")
        
        # 创建租户记录
        tenant = Tenant(
            name=tenant_in.name,
            schema_name="",  # 先设置为空，后面更新
            status=TenantStatus.ACTIVE,
            description=tenant_in.description,
            max_users=tenant_in.max_users,
            expire_date=tenant_in.expire_date
        )
        db.add(tenant)
        await db.flush()  # 获取自动生成的 ID
        logger.debug(f"租户记录已创建，ID: {tenant.id}")
        
        # 更新schema_name为tenant_{id}
        tenant.schema_name = f"tenant_{tenant.id}"
        await db.commit()
        logger.debug(f"租户 schema_name 已更新为: {tenant.schema_name}")
        
        # 初始化租户 schema 和表
        await init_tenant_schema(db, tenant.schema_name)
        
        # 记录审计日志
        await log_audit(
            user_id=current_user.id,
            action="create",
            resource_type="tenant",
            resource_id=tenant.id,
            details=f"创建新租户：{tenant.name}，最大用户数：{tenant.max_users}，到期时间：{tenant.expire_date}",
            request=request
        )
        
        # 使用 Pydantic 模型序列化租户数据
        tenant_response = TenantResponse.model_validate(tenant)
        return Success(data=tenant_response.model_dump())
        
    except Exception as e:
        # 如果发生错误，回滚事务
        await db.rollback()
        logger.error(f"创建租户失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建租户失败: {str(e)}"
        )

@router.put("/update")
async def update_tenant(
    request: Request,
    # tenant_id: int,
    tenant_in: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新租户信息
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_in.id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    # 允许被前端更新的字段
    ALLOWED_UPDATE_FIELDS = {"name", "description", "max_users", "expire_date", "status"}

    update_data = tenant_in.dict(exclude_unset=True)
    logger.debug(f"更新租户信息: {update_data}")
    for field in list(update_data.keys()):
        if field not in ALLOWED_UPDATE_FIELDS:
            update_data.pop(field)

    # expire_date 类型转换
    if 'expire_date' in update_data and update_data['expire_date']:
        if isinstance(update_data['expire_date'], str):
            from datetime import datetime
            update_data['expire_date'] = datetime.fromisoformat(update_data['expire_date']).date()

    for field, value in update_data.items():
        setattr(tenant, field, value)
        logger.debug(f"更新租户字段: {field} = {value}")
    
    await db.commit()
    await db.refresh(tenant)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="tenant",
        resource_id=tenant.id,
        details=f"更新租户：{tenant.name}，修改字段：{', '.join(update_data.keys())}",
        request=request
    )
    
    tenant_response = TenantResponse.model_validate(tenant)
    return Success(data=tenant_response.model_dump())

@router.delete("/delete")
async def delete_tenant(
    request: Request,
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
    
    tenant_name = tenant.name
    tenant.is_deleted = True
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="tenant",
        resource_id=tenant_id,
        details=f"删除租户：{tenant_name}",
        request=request
    )
    
    return Success(data={"message": "Tenant deleted successfully"}) 