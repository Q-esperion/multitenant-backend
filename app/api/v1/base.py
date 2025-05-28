from datetime import timedelta, datetime, timezone
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.security import create_access_token, verify_password, decrypt_password, get_password_hash, encrypt_password
from app.db.session import get_db
from app.models.public import User, Menu, Api, Role, RoleMenu, RoleApi, UserRole
from app.schemas.token import Token, LoginRequest, JWTPayload, JWTOut
from app.schemas.user import UserCreate, UserResponse, UserInfoResponse, UpdatePasswordRequest
from app.schemas.menu import MenuResponse
from app.schemas.common import Success, SuccessExtra, BaseSchema
from app.deps import get_current_user, get_current_active_superuser
from app.core.log import get_logger
from app.utils.audit import log_audit
import logging

router = APIRouter()
logger = get_logger(__name__)

@router.post("/access_token", summary="用户登录")
async def login_access_token(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        # 解密密码
        decrypted_password = decrypt_password(login_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码解密失败: {str(e)}"
        )

    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(decrypted_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    # 获取用户的租户信息
    tenant_id = None
    if not user.is_superuser:
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未分配租户"
            )
        tenant_id = user.tenant_id
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    jwt_payload = JWTPayload(
        user_id=user.id,
        username=user.username,
        is_superuser=user.is_superuser,
        tenant_id=tenant_id,
        exp=expire
    )

    data = JWTOut(
        access_token=create_access_token(data=jwt_payload.model_dump()),
        username=user.username,
        tenant_id=tenant_id
    )
    
    # 记录审计日志
    await log_audit(
        user_id=user.id,
        action="login",
        resource_type="base",
        resource_id=0,
        details=f"用户登录，用户名={user.username}",
        request=request
    )
    
    return Success(data=data.model_dump())

@router.get("/userinfo", summary="获取当前用户信息")
async def get_user_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前用户信息
    """
    # 获取用户角色
    result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == current_user.id)
    )
    roles = result.scalars().all()
    role_list = [{"id": role.id, "name": role.name} for role in roles]
    
    # 先创建基础用户数据
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "tenant_id": current_user.tenant_id,
        "is_tenant_admin": current_user.is_tenant_admin,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "roles": role_list
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="base",
        resource_id=current_user.id,
        details=f"查看用户信息：用户名={current_user.username}",
        request=request
    )
    
    return Success(data=user_data.model_dump())

@router.get("/usermenu", summary="获取当前用户菜单")
async def get_user_menu(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户的菜单"""
    # 如果是超级管理员，返回所有菜单
    if current_user.is_superuser:
        result = await db.execute(
            select(Menu)
            .where(Menu.is_deleted == False)
            .order_by(Menu.order)
        )
        menus = result.scalars().all()
    else:
        # 获取用户角色关联的菜单
        result = await db.execute(
            select(Menu)
            .join(RoleMenu)
            .join(Role)
            .join(Role.users)
            .where(User.id == current_user.id)
            .where(Menu.is_deleted == False)
            .order_by(Menu.order)
        )
        menus = result.scalars().all()
    
    # 构建树形结构
    menu_dict = {}
    root_menus = []
    
    # 第一次遍历：创建菜单字典和初始化 children 列表
    for menu in menus:
        menu_dict[menu.id] = {
            "id": menu.id,
            "name": menu.name,
            "title": menu.name,
            "menu_type": menu.menu_type,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "is_hidden": menu.is_hidden,
            "keepalive": menu.keepalive,
            "redirect": menu.redirect,
            "is_enabled": True,
            "children": []
        }
    
    # 第二次遍历：构建树形结构
    for menu in menus:
        menu_data = menu_dict[menu.id]
        if menu.parent_id is None:
            root_menus.append(menu_data)
        else:
            parent = menu_dict.get(menu.parent_id)
            if parent:
                parent["children"].append(menu_data)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="base",
        resource_id=0,
        details=f"查询用户菜单，用户名={current_user.username}",
        request=request
    )
    
    return Success(data=root_menus)

@router.get("/userapi", summary="获取当前用户API权限")
async def get_user_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取当前用户的API权限
    """
    # 如果是超级管理员，返回所有API
    if current_user.is_superuser:
        result = await db.execute(
            select(Api)
            .where(Api.is_deleted == False)
        )
        apis = result.scalars().all()
    else:
        # 获取用户角色关联的API
        result = await db.execute(
            select(Api)
            .join(RoleApi)
            .join(Role)
            .join(Role.users)
            .where(User.id == current_user.id)
            .where(Api.is_deleted == False)
        )
        apis = result.scalars().all()
    
    api_paths = [api.path for api in apis]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="base",
        resource_id=0,
        details=f"查询用户API权限，用户名={current_user.username}",
        request=request
    )
    
    return Success(data=api_paths)

@router.post("/update_password", summary="修改密码")
async def update_password(
    request: Request,
    password_data: UpdatePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    修改密码
    """
    try:
        # 解密旧密码和新密码
        old_password = decrypt_password(password_data.old_password)
        new_password = decrypt_password(password_data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码解密失败: {str(e)}"
        )
    
    # 验证旧密码
    if not verify_password(old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.password = get_password_hash(new_password)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="base",
        resource_id=current_user.id,
        details=f"更新密码，用户名={current_user.username}",
        request=request
    )
    
    return Success(data={"msg": "密码修改成功"}) 