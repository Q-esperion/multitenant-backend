"""
数据库会话管理
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app import async_session
from app.core.config import settings

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_tenant_db(tenant_id: int) -> AsyncGenerator[AsyncSession, None]:
    """
    获取租户数据库会话
    """
    schema_name = f"tenant_{tenant_id}"
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
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
            await engine.dispose() 