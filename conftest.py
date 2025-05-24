import os
import sys
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.db.base import Base
from app.core.config import Settings

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 设置测试环境变量
os.environ["POSTGRES_DB"] = "multi_tenant_test"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

# 创建测试配置
settings = Settings()

# 创建测试数据库引擎
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# 使用NullPool以避免连接池问题
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    poolclass=NullPool
)

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """创建一个事件循环，用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db():
    """创建测试数据库会话"""
    try:
        # 创建测试数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # 创建测试会话
        async with TestingSessionLocal() as session:
            yield session
        
        # 清理测试数据库
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise 