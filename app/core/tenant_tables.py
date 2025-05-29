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
        # 验证输入参数
        if not schema_name:
            raise ValueError("schema_name 不能为空")
        logger.info(f"开始初始化租户 Schema: {schema_name}")

        # 检查 Schema 是否已存在
        result = await db.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
        schema_exists = result.scalar()
        if schema_exists:
            logger.warning(f"Schema {schema_name} 已存在，将跳过创建步骤")
        else:
            # 创建 Schema
            logger.info(f"开始创建 Schema: {schema_name}")
            await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await db.commit()  # 提交创建 schema 的事务
            logger.info(f"Schema {schema_name} 创建成功")
            
            # 验证 schema 是否真的创建成功
            result = await db.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
            if not result.scalar():
                raise Exception(f"Schema {schema_name} 创建失败")
        
        # 切换到新 schema
        logger.info(f"开始切换到 Schema: {schema_name}")
        await db.execute(text(f"SET search_path TO {schema_name}"))
        await db.commit()  # 提交 schema 切换
        
        # 验证 schema 切换是否成功
        result = await db.execute(text("SELECT current_schema()"))
        current_schema = result.scalar()
        if current_schema != schema_name:
            raise Exception(f"Schema 切换失败，当前 schema: {current_schema}")
        logger.info(f"已成功切换到 Schema {schema_name}")
        
        # 创建所有表
        logger.info("开始创建租户表...")
        tables = [
            ("admission_batches", _create_admission_batches_table),
            ("departments", _create_departments_table),
            ("dormitories", _create_dormitories_table),
            ("students", _create_students_table),
            ("staff", _create_staff_table),
            ("registration_processes", _create_registration_processes_table),
            ("info_entry_processes", _create_info_entry_processes_table),
            ("registration_info", _create_registration_info_table),
            ("field_mappings", _create_field_mappings_table)
        ]
        
        for table_name, create_func in tables:
            try:
                logger.info(f"开始创建表 {table_name}")
                await create_func(db)
                await db.commit()  # 提交每个表的创建
                
                # 验证表是否创建成功
                result = await db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = '{schema_name}' 
                        AND table_name = '{table_name}'
                    )
                """))
                if not result.scalar():
                    raise Exception(f"表 {table_name} 创建失败")
                logger.info(f"表 {table_name} 创建成功")
            except Exception as e:
                logger.error(f"创建表 {table_name} 时发生错误: {str(e)}")
                await db.rollback()  # 发生错误时回滚
                raise
        
        # 切换回默认 schema
        logger.info("开始切换回 public schema")
        await db.execute(text("SET search_path TO public"))
        await db.commit()  # 提交 schema 切换
        
        # 验证是否成功切换回 public schema
        result = await db.execute(text("SELECT current_schema()"))
        current_schema = result.scalar()
        if current_schema != "public":
            raise Exception(f"切换回 public schema 失败，当前 schema: {current_schema}")
        logger.info("已成功切换回 public schema")
        
        # 最终验证
        logger.info("执行最终验证...")
        result = await db.execute(text(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}'
        """))
        table_count = result.scalar()
        logger.info(f"Schema {schema_name} 中的表数量: {table_count}")
        if table_count != len(tables):
            raise Exception(f"表数量不匹配，期望 {len(tables)} 个表，实际有 {table_count} 个表")
        
        logger.info(f"租户 Schema {schema_name} 初始化完成")
        
    except Exception as e:
        logger.error(f"初始化租户 Schema 失败: {str(e)}", exc_info=True)
        await db.rollback()  # 发生错误时回滚
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