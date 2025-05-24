"""
Multi-tenant Campus Freshman Registration System
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent

# 将项目根目录添加到 Python 路径
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(ROOT_DIR))

# 版本信息
__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 导入配置
from app.core.config import settings

# 创建数据库引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# 创建异步会话工厂
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 导入模型
from app.models.public import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 初始化数据
    from app.db.init_data import init_data
    await init_data()
    
    yield
    
    # 关闭数据库连接
    await engine.dispose()

def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Multi-tenant Campus Freshman Registration System",
        version=__version__,
        lifespan=lifespan,
    )
    
    # 注册路由
    from app.api.v1 import base
    app.include_router(base.router, prefix=settings.API_V1_STR)
    
    # 注册中间件
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

# 创建应用实例
app = create_app()

# 导出常用模块
__all__ = [
    "settings",
    "async_session",
    "engine",
    "Base",
    "app",
] 