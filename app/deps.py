from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db, get_tenant_db
from app.models.public import User
from app.core.log import get_logger

# 获取logger
logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/access_token")

async def get_current_user(
    token: str = Header(None, description="token验证"),
    authorization: str = Header(None, description="Authorization验证"),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户
    支持从token或Authorization头部获取token
    返回:
        User: 当前用户对象
    """
    try:
        # 获取token值
        token_value = None
        if token:
            token_value = token
            logger.debug("从token头部获取token")
        elif authorization:
            if authorization.startswith("Bearer "):
                token_value = authorization.split(" ")[1]
                logger.debug("从Authorization头部获取Bearer token")
            else:
                token_value = authorization
                logger.debug("从Authorization头部获取token")
                
        if not token_value:
            logger.warning("未提供认证信息")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证信息"
            )
            
        if token_value == "dev":
            logger.debug("使用开发模式token")
            result = await db.execute(select(User))
            user = result.scalar_one_or_none()
            return user
            
        try:
            logger.debug("开始解码token")
            payload = jwt.decode(
                token_value, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
        except JWTError as e:
            if isinstance(e, jwt.ExpiredSignatureError):
                logger.warning("token已过期")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="登录已过期"
                )
            logger.error(f"token解码失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token"
            )
            
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("token中未找到user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token"
            )
            
        logger.debug(f"查询用户ID: {user_id}")
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
            
        logger.info(f"用户认证成功: {user.username}")
        return user
    except Exception as e:
        logger.error(f"用户认证过程发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

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