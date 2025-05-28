# app/core/tenant_tables.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.log import get_logger

logger = get_logger(__name__)

async def init_tenant_schema(db: AsyncSession, schema_name: str) -> None:
    """
    初始化租户 Schema 和所有必要的表
    
    Args:
        db: 数据库会话
        schema_name: 租户的 schema 名称
    """
    try:
        # 创建 Schema
        logger.debug(f"开始创建 Schema: {schema_name}")
        await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        logger.debug(f"Schema {schema_name} 创建成功")
        
        # 切换到新 schema
        logger.debug(f"开始切换到 Schema: {schema_name}")
        await db.execute(text(f"SET search_path TO {schema_name}"))
        logger.debug(f"已切换到 Schema {schema_name}")
        
        # 创建所有表
        await _create_admission_batches_table(db)
        await _create_departments_table(db)
        await _create_dormitories_table(db)
        await _create_students_table(db)
        await _create_staff_table(db)
        await _create_registration_processes_table(db)
        await _create_info_entry_processes_table(db)
        await _create_registration_info_table(db)
        await _create_field_mappings_table(db)
        
        # 切换回默认 schema
        logger.debug("开始切换回 public schema")
        await db.execute(text("SET search_path TO public"))
        logger.debug("已切换回 public schema")
        
    except Exception as e:
        logger.error(f"初始化租户 Schema 失败: {str(e)}")
        raise

async def _create_admission_batches_table(db: AsyncSession) -> None:
    """创建录取批次表"""
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

async def _create_departments_table(db: AsyncSession) -> None:
    """创建部门表"""
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

async def _create_dormitories_table(db: AsyncSession) -> None:
    """创建宿舍表"""
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

async def _create_students_table(db: AsyncSession) -> None:
    """创建学生表"""
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

async def _create_staff_table(db: AsyncSession) -> None:
    """创建教职工表"""
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

async def _create_registration_processes_table(db: AsyncSession) -> None:
    """创建注册流程表"""
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

async def _create_info_entry_processes_table(db: AsyncSession) -> None:
    """创建信息录入流程表"""
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

async def _create_registration_info_table(db: AsyncSession) -> None:
    """创建注册信息表"""
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

async def _create_field_mappings_table(db: AsyncSession) -> None:
    """创建字段映射表"""
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