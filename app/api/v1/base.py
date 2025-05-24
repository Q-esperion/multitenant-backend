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
from app.schemas.common import Success
from app.api.v1 import user, role, menu, api, tenant, log
from app.deps import get_current_user, get_current_active_superuser
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 注册所有子路由
router.include_router(user.router, prefix="/user", tags=["user"])
router.include_router(role.router, prefix="/role", tags=["role"])
router.include_router(menu.router, prefix="/menu", tags=["menu"])
router.include_router(api.router, prefix="/api", tags=["api"])
router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
router.include_router(log.router, prefix="/log", tags=["log"])

@router.post("/access_token", response_model=Success[JWTOut])
async def login_access_token(
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
    
    return Success(data=data.model_dump())

@router.get("/userinfo", response_model=Success[UserInfoResponse])
async def get_user_info(
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
    role_names = [role.name for role in roles]
    
    user_info = UserInfoResponse(
        **current_user.__dict__,
        roles=role_names
    )
    
    return Success(data=user_info)

@router.get("/usermenu", response_model=Success[List[MenuResponse]])
async def get_user_menu(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户的菜单"""
    # 如果是超级管理员，返回所有菜单
    if current_user.is_superuser:
        result = await db.execute(
            select(Menu)
            .order_by(Menu.order)
        )
        menus = result.scalars().all()
    else:
        # 获取用户角色
        result = await db.execute(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == current_user.id)
        )
        roles = result.scalars().all()
        
        # 检查是否有系统管理员角色
        is_admin = any(role.code == "admin" for role in roles)
        if is_admin:
            # 系统管理员返回所有菜单
            result = await db.execute(
                select(Menu)
                .order_by(Menu.order)
            )
            menus = result.scalars().all()
        else:
            # 获取角色对应的菜单
            menu_ids = set()
            for role in roles:
                result = await db.execute(
                    select(RoleMenu.menu_id)
                    .where(RoleMenu.role_id == role.id)
                )
                role_menu_ids = result.scalars().all()
                menu_ids.update(role_menu_ids)
            
            # 获取所有菜单
            result = await db.execute(
                select(Menu)
                .where(Menu.id.in_(menu_ids))
                .order_by(Menu.order)
            )
            menus = result.scalars().all()
    
    # 构建菜单树
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
    
    return Success(data=root_menus)

@router.get("/userapi", response_model=Success[List[str]])
async def get_user_api(
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
    return Success(data=api_paths)

@router.post("/update_password", response_model=Success[dict])
async def update_password(
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
    
    return Success(data={"msg": "密码修改成功"})

@router.post("/register", response_model=Success[UserResponse])
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register new user.
    """
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    
    user = User(
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return Success(data=user)

@router.post("/user/create", response_model=Success[UserResponse])
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    创建用户
    """
    try:
        logger.info(f"开始创建用户，请求数据: {user_in.dict()}")
        
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_in.username)
        )
        if result.scalar_one_or_none():
            logger.error(f"用户名已存在: {user_in.username}")
            raise HTTPException(
                status_code=400,
                detail="用户名已存在"
            )
        
        # 检查租户是否存在
        if user_in.tenant_id:
            result = await db.execute(
                select(User).where(User.id == user_in.tenant_id)
            )
            if not result.scalar_one_or_none():
                logger.error(f"租户不存在: {user_in.tenant_id}")
                raise HTTPException(
                    status_code=400,
                    detail="租户不存在"
                )
        
        # 创建用户
        user = User(
            username=user_in.username,
            password=encrypt_password(user_in.password),
            email=user_in.email,
            phone=user_in.phone,
            is_active=user_in.is_active,
            user_type=user_in.user_type,
            tenant_id=user_in.tenant_id,
            is_tenant_admin=user_in.is_tenant_admin
        )
        
        db.add(user)
        await db.flush()
        
        # 如果指定了角色，为用户分配角色
        if user_in.role_ids:
            for role_id in user_in.role_ids:
                user_role = UserRole(user_id=user.id, role_id=role_id)
                db.add(user_role)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"用户创建成功: {user.username}")
        return Success(data=user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建用户失败: {str(e)}"
        ) 