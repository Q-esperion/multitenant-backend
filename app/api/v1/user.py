from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.deps import get_current_user
from app.models.public import User, Role, UserRole, Tenant
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserInfoResponse, ResetPasswordRequest
from app.schemas.common import Success, SuccessExtra, BaseSchema
from app.core.security import get_password_hash, decrypt_password
from app.utils.audit import log_audit
from app.core.log import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/create", summary="创建用户")
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建新用户
    """
    logger.debug(f"开始创建用户: {user_in.username}")
    
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # 权限校验
    if current_user.is_superuser:
        # 超级管理员可以为所有租户创建用户
        pass
    elif current_user.is_tenant_admin:
        # 租户管理员只能为自己租户创建用户
        if user_in.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="租户管理员只能为自己租户创建用户"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="没有创建用户的权限"
        )
    
    try:
        # 解密密码
        decrypted_password = decrypt_password(user_in.password)
        logger.debug(f"解密密码: {decrypted_password}")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"密码解密失败: {str(e)}"
        )
    
    # 创建新用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        phone=user_in.phone,
        password=get_password_hash(decrypted_password),
        # password=user_in.password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        tenant_id=user_in.tenant_id,
        is_tenant_admin=user_in.is_tenant_admin
    )
    
    try:
        db.add(user)
        await db.flush()
        logger.debug(f"用户记录已创建，ID: {user.id}")
        
        # 如果指定了角色，为用户分配角色
        if user_in.role_ids:
            for role_id in user_in.role_ids:
                user_role = UserRole(user_id=user.id, role_id=role_id)
                db.add(user_role)
            logger.debug(f"已为用户分配 {len(user_in.role_ids)} 个角色")
        
        await db.commit()
        await db.refresh(user)
        
        # 获取用户角色信息
        role_result = await db.execute(
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user.id)
        )
        roles = role_result.scalars().all()
        user_roles = [
            {"id": role.id, "name": role.name}
            for role in roles
        ]
        
        # 记录审计日志
        await log_audit(
            user_id=current_user.id,
            action="create",
            resource_type="user",
            resource_id=user.id,
            details=f"创建新用户：{user.username}",
            request=request
        )
        
        # 创建基础用户数据字典
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
            "is_tenant_admin": user.is_tenant_admin,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": user_roles
        }
        
        # 使用 Pydantic 模型验证和序列化数据
        user_data = UserInfoResponse.model_validate(user_dict)
        logger.info(f"用户 {user.username} 创建成功")
        return Success(data=user_data.model_dump())
    except Exception as e:
        await db.rollback()
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建用户失败: {str(e)}"
        )

@router.get("/list", summary="获取用户列表")
async def get_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: str = None,
    email: str = None,
    phone: str = None,
    status: bool = None
) -> Any:
    """
    获取用户列表
    """
    # 修改查询，包含租户信息
    query = select(User, Tenant.name.label('tenant_name')).outerjoin(Tenant, User.tenant_id == Tenant.id)
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
    if phone:
        query = query.where(User.phone == phone)
    if status is not None:
        query = query.where(User.is_active == status)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users_with_tenant = result.all()
    
    # 获取用户角色信息
    user_roles = {}
    for user, _ in users_with_tenant:
        role_result = await db.execute(
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user.id)
        )
        roles = role_result.scalars().all()
        user_roles[user.id] = [
            {"id": role.id, "name": role.name}
            for role in roles
        ]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="user",
        resource_id=0,
        details=f"查询用户列表，筛选条件：用户名={username}, 邮箱={email}, 手机号={phone}, 状态={status}",
        request=request
    )
    
    # 使用 Pydantic 模型序列化用户数据
    user_list = []
    for user, tenant_name in users_with_tenant:
        # 创建基础用户数据字典
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
            "tenant_name": tenant_name,  # 添加租户名称
            "is_tenant_admin": user.is_tenant_admin,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": user_roles.get(user.id, [])
        }
        
        # 使用 Pydantic 模型验证和序列化数据
        user_data = UserInfoResponse.model_validate(user_dict)
        user_list.append(user_data.model_dump())
    
    return SuccessExtra(data=user_list, total=total, page=page, page_size=page_size)

@router.get("/get", summary="获取用户详情")
async def get_user(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取用户详情
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # 获取用户角色信息
    role_result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user.id)
    )
    roles = role_result.scalars().all()
    user_roles = [
        {"id": role.id, "name": role.name}
        for role in roles
    ]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="user",
        resource_id=user.id,
        details=f"查看用户详情：{user.username}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": user_roles
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.post("/update", summary="更新用户")
async def update_user(
    request: Request,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户信息
    """
    result = await db.execute(select(User).where(User.id == user_in.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        try:
            # 解密密码
            decrypted_password = decrypt_password(update_data["password"])
            update_data["password"] = get_password_hash(decrypted_password)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"密码解密失败: {str(e)}"
            )
    
    for field, value in update_data.items():
        if field != "role_ids":  # 角色单独处理
            setattr(user, field, value)
    
    # 更新用户角色
    if "role_ids" in update_data:
        # 删除原有角色
        await db.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user.id)
        )
        # 添加新角色
        for role_id in update_data["role_ids"]:
            user_role = UserRole(user_id=user.id, role_id=role_id)
            db.add(user_role)
    
    await db.commit()
    await db.refresh(user)
    
    # 获取用户角色信息
    role_result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user.id)
    )
    roles = role_result.scalars().all()
    user_roles = [
        {"id": role.id, "name": role.name}
        for role in roles
    ]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户：{user.username}，修改字段：{', '.join(update_data.keys())}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": user_roles
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.delete("/delete", summary="删除用户")
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除用户
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="delete",
        resource_type="user",
        resource_id=user_id,
        details=f"删除用户：{user.username}",
        request=request
    )
    
    return Success(data={"message": "User deleted successfully"})

@router.post("/reset_password", summary="重置用户密码")
async def reset_password(
    request: Request,
    # user_id: int,
    # password_data: ResetPasswordRequest = None,
    password_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    重置用户密码
    1. 如果提供new_password，则使用新密码（需要满足密码复杂度要求）
    2. 如果不提供new_password，则重置为默认密码（Admin@123456）
    """
    # 检查权限
    if not current_user.is_superuser and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=403,
            detail="没有重置密码的权限"
        )
    
    # 获取用户
    result = await db.execute(select(User).where(User.id == password_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    # 租户管理员只能重置自己租户的用户密码
    if current_user.is_tenant_admin and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="只能重置自己租户的用户密码"
        )
    
    if password_data.new_password:
        try:
            # 解密新密码
            decrypted_password = decrypt_password(password_data.new_password)
            # 更新密码
            user.password = get_password_hash(decrypted_password)
            success_message = "密码重置成功"
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"密码解密失败: {str(e)}"
            )
    else:
        # 使用默认密码（Admin@123456）
        user.password = get_password_hash("Admin@123456")
        success_message = "密码已重置为默认密码（Admin@123456）"
    
    await db.commit()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户密码：{user.username}",
        request=request
    )
    
    return Success(data={"message": success_message})

@router.put("/update_status", summary="更新用户状态")
async def update_user_status(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户状态
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户状态：{user.username}，新状态：{user.is_active}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": []
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.put("/update_roles", summary="更新用户角色")
async def update_user_roles(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户角色
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "role_ids" in update_data:
        # 删除原有角色
        await db.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user.id)
        )
        # 添加新角色
        for role_id in update_data["role_ids"]:
            user_role = UserRole(user_id=user.id, role_id=role_id)
            db.add(user_role)
    
    await db.commit()
    await db.refresh(user)
    
    # 获取用户角色信息
    role_result = await db.execute(
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user.id)
    )
    roles = role_result.scalars().all()
    user_roles = [
        {"id": role.id, "name": role.name}
        for role in roles
    ]
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户角色：{user.username}，角色ID：{', '.join(map(str, update_data['role_ids']))}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": user_roles
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.put("/update_menus", summary="更新用户菜单权限")
async def update_user_menus(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户菜单权限
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "menu_ids" in update_data:
        user.menu_ids = update_data["menu_ids"]
    
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户菜单权限：{user.username}，菜单ID：{', '.join(map(str, update_data['menu_ids']))}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": []
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.put("/update_apis", summary="更新用户API权限")
async def update_user_apis(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户API权限
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "api_ids" in update_data:
        user.api_ids = update_data["api_ids"]
    
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户API权限：{user.username}，API ID：{', '.join(map(str, update_data['api_ids']))}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": []
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump())

@router.put("/update_tenants", summary="更新用户租户权限")
async def update_user_tenants(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户租户权限
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "tenant_ids" in update_data:
        user.tenant_ids = update_data["tenant_ids"]
    
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=user.id,
        details=f"更新用户租户权限：{user.username}，租户ID：{', '.join(map(str, update_data['tenant_ids']))}",
        request=request
    )
    
    # 创建基础用户数据字典
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "is_tenant_admin": user.is_tenant_admin,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": []
    }
    
    # 使用 Pydantic 模型验证和序列化数据
    user_data = UserInfoResponse.model_validate(user_dict)
    
    return Success(data=user_data.model_dump()) 