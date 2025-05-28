"""
数据库同步工具
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
from app.core.log import get_logger

logger = get_logger(__name__)

async def sync_database():
    """
    同步数据库结构
    """
    try:
        async with engine.begin() as conn:
            # 获取所有现有表
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            existing_tables = {row[0] for row in result}
            
            # 获取所有模型表
            model_tables = {table.name for table in Base.metadata.tables.values()}
            
            # 删除不存在的表
            tables_to_drop = existing_tables - model_tables
            for table in tables_to_drop:
                logger.info(f"删除不存在的表: {table}")
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            
            # 创建或更新表结构
            logger.info("开始同步数据库结构...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库结构同步完成")
            
            # 更新序列
            for table in model_tables:
                try:
                    await conn.execute(text(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
                            false
                        )
                    """))
                except Exception as e:
                    logger.warning(f"更新表 {table} 的序列失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"同步数据库结构失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(sync_database())