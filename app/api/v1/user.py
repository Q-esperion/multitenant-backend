from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.deps import get_current_user
from app.models.public import User
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.schemas.common import Success
from app.core.security import get_password_hash, decrypt_password
from app.utils.audit import log_audit

router = APIRouter()

@router.post("/create", response_model=Success[UserResponse])
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    创建新用户
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    try:
        # 解密密码
        decrypted_password = decrypt_password(user_in.password)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"密码解密失败: {str(e)}"
        )
    
    # 创建新用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        password=get_password_hash(decrypted_password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        user_type=user_in.user_type,
        tenant_id=current_user.tenant_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="create",
        resource_type="user",
        resource_id=user.id,
        details=f"Created new user: {user.username}",
        request=request
    )
    
    return Success(data=user)

@router.get("/list", response_model=Success[dict])
async def get_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: str = None
) -> Any:
    """
    获取用户列表
    """
    query = select(User)
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="list",
        resource_type="user",
        resource_id=0,
        details=f"Listed users with filters: username={username}",
        request=request
    )
    
    return Success(data={
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@router.get("/get", response_model=Success[UserResponse])
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
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="get",
        resource_type="user",
        resource_id=id,
        details=f"Viewed user details",
        request=request
    )
    
    return Success(data=user)

@router.put("/update", response_model=Success[UserResponse])
async def update_user(
    request: Request,
    id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    更新用户信息
    """
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    update_data = user_in.dict(exclude_unset=True)
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
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    # 记录审计日志
    await log_audit(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=id,
        details=f"Updated user fields: {', '.join(update_data.keys())}",
        request=request
    )
    
    return Success(data=user)

@router.delete("/delete", response_model=Success[dict])
async def delete_user(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    删除用户
    """
    result = await db.execute(select(User).where(User.id == id))
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
        resource_id=id,
        details=f"Deleted user",
        request=request
    )
    
    return Success(data={"message": "User deleted successfully"}) 