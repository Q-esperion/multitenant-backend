from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.security import verify_token
from app.models.public import AccessLog
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
import time
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
    ):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        path = request.url.path
        method = request.method
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 获取用户信息
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = verify_token(token)
                if payload:
                    username = payload.get("sub")
                    if username:
                        async with async_session() as session:
                            from app.models.public import User
                            from sqlalchemy import select
                            result = await session.execute(
                                select(User).where(User.username == username)
                            )
                            user = result.scalar_one_or_none()
                            if user:
                                user_id = user.id
            except Exception:
                pass

        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        process_time = int((time.time() - start_time) * 1000)
        
        try:
            # 创建访问日志
            access_log = AccessLog(
                user_id=user_id,
                path=path,
                method=method,
                status_code=response.status_code,
                response_time=process_time,
                ip_address=client_host,
                user_agent=user_agent
            )
            
            # 异步保存日志
            async with async_session() as session:
                session.add(access_log)
                await session.commit()
        except Exception as e:
            # 如果记录日志失败，打印错误信息但不影响请求处理
            print(f"Failed to log access: {str(e)}")
        
        return response 