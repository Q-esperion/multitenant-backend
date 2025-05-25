"""
更新数据库时间字段为带时区的时间格式
"""

from sqlalchemy import text
from app.db.session import engine
from app.core.log import get_logger

logger = get_logger(__name__)

async def update_timezone_columns():
    """更新所有时间字段为带时区的时间格式"""
    try:
        async with engine.begin() as conn:
            # 获取当前数据库名称
            result = await conn.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            
            # 设置数据库时区
            await conn.execute(text(f"ALTER DATABASE {db_name} SET timezone TO 'Asia/Shanghai';"))
            
            # 更新 users 表
            await conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai',
                ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'Asia/Shanghai',
                ALTER COLUMN last_login TYPE TIMESTAMP WITH TIME ZONE USING last_login AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 更新 apis 表
            await conn.execute(text("""
                ALTER TABLE apis 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai',
                ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 更新 menus 表
            await conn.execute(text("""
                ALTER TABLE menus 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai',
                ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 更新 tenant_permissions 表
            await conn.execute(text("""
                ALTER TABLE tenant_permissions 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai',
                ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 更新 audit_logs 表
            await conn.execute(text("""
                ALTER TABLE audit_logs 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 更新 access_logs 表
            await conn.execute(text("""
                ALTER TABLE access_logs 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai';
            """))
            
            # 设置会话时区
            await conn.execute(text("SET timezone = 'Asia/Shanghai';"))
            
            logger.info("数据库时间字段更新成功")
    except Exception as e:
        logger.error(f"更新数据库时间字段失败: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(update_timezone_columns()) 