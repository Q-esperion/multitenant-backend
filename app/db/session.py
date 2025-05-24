from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    future=True
)

# 创建异步会话工厂
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖函数
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_tenant_db(tenant_id: int):
    schema_name = f"tenant_{tenant_id}"
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        connect_args={"options": f"-csearch_path={schema_name}"}
    )
    
    AsyncTenantSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with AsyncTenantSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 