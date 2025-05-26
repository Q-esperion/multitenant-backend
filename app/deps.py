from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import ValidationError
from app.core.config import settings
from app.db.session import get_db, get_tenant_db
from app.models.public import User, Api, Role, RoleApi, TenantPermission, Menu, RoleMenu
from app.core.log import get_logger
from app.schemas.token import JWTPayload

# 获取logger
logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/base/access_token")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = JWTPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户
    """
    if not current_user.is_active:
        logger.warning(f"用户未激活: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    logger.debug(f"获取活跃用户: {current_user.username}")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前超级用户
    """
    if not current_user.is_superuser:
        logger.warning(f"非超级用户尝试访问超级用户接口: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    logger.debug(f"获取超级用户: {current_user.username}")
    return current_user

async def get_current_tenant_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前租户管理员用户"""
    if not current_user.is_tenant_admin:
        logger.warning(f"非租户管理员尝试访问管理员接口: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    logger.debug(f"获取租户管理员: {current_user.username}")
    return current_user

async def get_tenant_session(
    tenant_id: int,
    db: AsyncSession = Depends(get_db)
) -> Generator[AsyncSession, None, None]:
    """获取租户数据库会话"""
    logger.debug(f"获取租户数据库会话: tenant_id={tenant_id}")
    async for session in get_tenant_db(tenant_id):
        yield session 

async def check_permission(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    权限校验依赖函数
    1. 检查用户是否登录（通过get_current_user依赖）
    2. 如果是超级管理员，直接放行
    3. 检查租户权限
    4. 检查用户角色权限
    """
    # 如果是超级管理员，直接放行
    if current_user.is_superuser:
        return

    # 获取当前请求的路径和方法
    path = request.url.path
    method = request.method

    # 检查租户权限
    tenant_permission_query = select(TenantPermission).join(Api).where(
        and_(
            TenantPermission.tenant_id == current_user.tenant_id,
            Api.path == path,
            Api.method == method,
            TenantPermission.is_enabled == True,
            TenantPermission.is_deleted == False
        )
    )
    tenant_permission = await db.scalar(tenant_permission_query)
    if not tenant_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="租户没有访问权限"
        )

    # 检查用户角色权限
    role_api_query = select(RoleApi).join(Role).join(User).where(
        and_(
            User.id == current_user.id,
            RoleApi.api_id == tenant_permission.api_id
        )
    )
    role_api = await db.scalar(role_api_query)
    if not role_api:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户角色没有访问权限"
        ) 