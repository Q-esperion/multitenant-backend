from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import base
from app.middleware.logging import LoggingMiddleware
from app.core.log import get_logger

# 获取logger
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
if settings.CORS_ORIGINS:
    logger.debug("配置CORS中间件")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 添加日志中间件
logger.debug("添加日志中间件")
app.add_middleware(LoggingMiddleware)

# 注册路由
logger.debug("注册基础路由")
app.include_router(base.router, prefix=f"{settings.API_V1_STR}/base")

@app.get("/")
async def root():
    logger.info("访问根路径")
    return {"message": "Welcome to Multi-tenant Campus Registration System"} 