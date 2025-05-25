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
from fastapi.middleware.cors import CORSMiddleware

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
    echo=settings.DEBUG,
    connect_args={
        "server_settings": {
            "timezone": "Asia/Shanghai"
        }
    }
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
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
    
    yield
    
    # 关闭数据库连接
    await engine.dispose()

def create_app() -> FastAPI:
    """
    创建FastAPI应用
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # 配置CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 添加日志中间件
    from app.middleware.logging import LoggingMiddleware
    app.add_middleware(LoggingMiddleware)
    
    # 注册路由
    from app.api.v1.router import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")
    
    return app

# 创建应用实例
app = create_app()

# 导出常用模块
__all__ = [
    "settings",
    "AsyncSessionLocal",
    "engine",
    "Base",
    "app",
] 