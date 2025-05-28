"""
更新API数据脚本
"""

import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.public import Api
from app.core.log import get_logger
from app.utils.router_parser import generate_api_from_router
from app.api.v1.router import router as api_v1_router

logger = get_logger(__name__)

async def update_api():
    """更新API数据"""
    try:
        async with AsyncSessionLocal() as session:
            # 获取所有API路由
            apis = generate_api_from_router(api_v1_router)
            
            # 获取现有的API记录
            result = await session.execute(select(Api))
            existing_apis = {api.path: api for api in result.scalars().all()}
            
            # 更新或创建API记录
            for api_data in apis:
                if api_data["path"] in existing_apis:
                    # 更新现有API
                    api = existing_apis[api_data["path"]]
                    api.method = api_data["method"]
                    api.summary = api_data["summary"]
                    api.tags = api_data["tags"]
                    api.updated_at = datetime.now()
                else:
                    # 创建新API
                    api = Api(
                        path=api_data["path"],
                        method=api_data["method"],
                        summary=api_data["summary"],
                        tags=api_data["tags"],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(api)
            
            # 标记已删除的API
            current_paths = {api["path"] for api in apis}
            for path, api in existing_apis.items():
                if path not in current_paths:
                    api.is_deleted = True
                    api.updated_at = datetime.now()
            
            await session.commit()
            logger.info("API数据更新完成")
    except Exception as e:
        await session.rollback()
        logger.error(f"API数据更新失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(update_api()) 