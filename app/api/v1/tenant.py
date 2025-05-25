from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db.session import get_db
from app.deps import get_current_user, get_current_active_superuser
from app.models.public import Tenant, User, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.schemas.common import Success, SuccessExtra
from app.core.log import get_logger
from datetime import date

router = APIRouter()
logger = get_logger(__name__)

@router.get("/list")
async def get_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
) -> Any:
    """
    获取租户列表
    """
    logger.debug(f"开始获取租户列表，页码: {page}, 每页数量: {page_size}")
    query = select(Tenant).where(Tenant.is_deleted == False)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tenants = result.scalars().all()
    logger.debug(f"查询到 {len(tenants)} 个租户")
    
    return SuccessExtra(data=tenants, total=total, page=page, page_size=page_size)

@router.post("/create")
async def create_tenant(
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
        
        # 创建租户schema
        schema_name = tenant.schema_name
        try:
            logger.debug(f"开始创建 Schema: {schema_name}")
            await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            logger.debug(f"Schema {schema_name} 创建成功")
        except Exception as e:
            logger.error(f"创建 Schema {schema_name} 失败: {str(e)}")
            raise
        
        # 切换到新schema并创建表
        try:
            logger.debug(f"开始切换到 Schema: {schema_name}")
            await db.execute(text(f"SET search_path TO {schema_name}"))
            logger.debug(f"已切换到 Schema {schema_name}")
        except Exception as e:
            logger.error(f"切换 Schema {schema_name} 失败: {str(e)}")
            raise
        
        # 创建租户特定的表
        try:
            # 1. 创建 admission_batches 表
            logger.debug("开始创建 admission_batches 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS admission_batches (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    description VARCHAR(500),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("admission_batches 表创建成功")
            
            # 2. 创建 departments 表
            logger.debug("开始创建 departments 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(50) UNIQUE,
                    parent_id INTEGER,
                    "order" INTEGER DEFAULT 0,
                    leader VARCHAR(50),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("departments 表创建成功")
            
            # 3. 创建 dormitories 表
            logger.debug("开始创建 dormitories 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS dormitories (
                    id SERIAL PRIMARY KEY,
                    building VARCHAR(50) NOT NULL,
                    room_number VARCHAR(20) NOT NULL,
                    capacity INTEGER DEFAULT 4,
                    current_count INTEGER DEFAULT 0,
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("dormitories 表创建成功")
            
            # 4. 创建 students 表
            logger.debug("开始创建 students 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS students (
                    id_card VARCHAR(18) PRIMARY KEY,
                    student_id VARCHAR(50) UNIQUE,
                    name VARCHAR(50) NOT NULL,
                    gender VARCHAR(10),
                    birth_date DATE,
                    admission_batch_id INTEGER,
                    department_id INTEGER,
                    dormitory_id INTEGER,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    address VARCHAR(200),
                    status BOOLEAN DEFAULT TRUE,
                    ext_field1 VARCHAR(200),
                    ext_field2 VARCHAR(200),
                    ext_field3 VARCHAR(200),
                    ext_field4 VARCHAR(200),
                    ext_field5 VARCHAR(200),
                    ext_field6 VARCHAR(200),
                    ext_field7 VARCHAR(200),
                    ext_field8 VARCHAR(200),
                    ext_field9 VARCHAR(200),
                    ext_field10 VARCHAR(200),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("students 表创建成功")
            
            # 5. 创建 staff 表
            logger.debug("开始创建 staff 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS staff (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    gender VARCHAR(10),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    department_id INTEGER,
                    position VARCHAR(50),
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("staff 表创建成功")
            
            # 6. 创建 registration_processes 表
            logger.debug("开始创建 registration_processes 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS registration_processes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    "order" INTEGER NOT NULL,
                    description VARCHAR(500),
                    is_required BOOLEAN DEFAULT TRUE,
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("registration_processes 表创建成功")
            
            # 6.1 创建 info_entry_processes 表
            logger.debug("开始创建 info_entry_processes 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS info_entry_processes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    "order" INTEGER NOT NULL,
                    description VARCHAR(500),
                    is_required BOOLEAN DEFAULT TRUE,
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("info_entry_processes 表创建成功")
            
            # 7. 创建 registration_info 表
            logger.debug("开始创建 registration_info 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS registration_info (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    process_id INTEGER NOT NULL,
                    status BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    operator_id INTEGER,
                    remarks TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("registration_info 表创建成功")
            
            # 8. 创建 field_mappings 表
            logger.debug("开始创建 field_mappings 表")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS field_mappings (
                    id SERIAL PRIMARY KEY,
                    field_name VARCHAR(50) NOT NULL,
                    display_name VARCHAR(50) NOT NULL,
                    is_required BOOLEAN DEFAULT FALSE,
                    "order" INTEGER DEFAULT 0,
                    status BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.debug("field_mappings 表创建成功")
            
            # 切换回默认schema
            logger.debug("开始切换回 public schema")
            await db.execute(text("SET search_path TO public"))
            logger.debug("已切换回 public schema")
            
            # 提交所有更改
            await db.commit()
            logger.info(f"租户 {tenant.name} 创建成功")
            
            # 使用 Pydantic 模型序列化租户数据
            tenant_response = TenantResponse.model_validate(tenant)
            return Success(data=tenant_response.model_dump())
        except Exception as e:
            logger.error(f"创建表失败: {str(e)}")
            raise
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

@router.delete("/delete")
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