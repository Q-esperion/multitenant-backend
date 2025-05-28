"""
初始化数据库表结构
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from sqlalchemy import text, inspect
from app.db.session import engine
from app.db.base import Base
from app.core.log import get_logger

# 显式导入所有模型
from app.models.public import (
    User, Role, Menu, Api, Tenant, 
    TenantPermission, AuditLog, AccessLog,
    RoleMenu, RoleApi, UserRole
)

logger = get_logger(__name__)

async def init_database():
    """
    初始化数据库表结构
    """
    try:
        # 打印所有已注册的表
        logger.info("已注册的表:")
        for table in Base.metadata.tables.values():
            logger.info(f"- {table.name}")
            for column in table.columns:
                logger.info(f"  - {column.name}: {column.type}")

        async with engine.begin() as conn:
            # 检查数据库连接
            logger.info("检查数据库连接...")
            await conn.execute(text("SELECT 1"))
            logger.info("数据库连接正常")
            
            # 获取现有表
            logger.info("获取现有表...")
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            existing_tables = {row[0] for row in result}
            logger.info(f"现有表: {existing_tables}")
            
            # 获取要创建的表
            tables_to_create = set(Base.metadata.tables.keys())
            logger.info(f"需要创建的表: {tables_to_create}")
            
            if not tables_to_create:
                logger.error("没有检测到需要创建的表！")
                logger.info("检查模型导入...")
                for model in [User, Role, Menu, Api, Tenant, TenantPermission, AuditLog, AccessLog, RoleMenu, RoleApi, UserRole]:
                    logger.info(f"模型 {model.__name__} 已导入")
                return
            
            # 创建所有表
            logger.info("开始创建数据库表...")
            try:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("数据库表创建完成")
            except Exception as e:
                logger.error(f"创建表失败: {str(e)}")
                # 尝试逐个创建表
                for table_name in tables_to_create:
                    if table_name not in existing_tables:
                        try:
                            logger.info(f"尝试创建表: {table_name}")
                            table = Base.metadata.tables[table_name]
                            await conn.run_sync(lambda sync_conn: table.create(sync_conn))
                            logger.info(f"表 {table_name} 创建成功")
                        except Exception as table_error:
                            logger.error(f"创建表 {table_name} 失败: {str(table_error)}")
                            raise
            
            # 创建序列
            logger.info("开始创建序列...")
            for table in Base.metadata.tables.values():
                try:
                    await conn.execute(text(f"""
                        CREATE SEQUENCE IF NOT EXISTS {table.name}_id_seq
                        START WITH 1
                        INCREMENT BY 1
                        NO MINVALUE
                        NO MAXVALUE
                        CACHE 1;
                    """))
                    logger.info(f"创建序列: {table.name}_id_seq")
                except Exception as e:
                    logger.warning(f"创建序列 {table.name}_id_seq 失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"初始化数据库失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())