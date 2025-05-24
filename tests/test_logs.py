import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.core.security import create_access_token
from app.models.public import User, AccessLog, AuditLog
from app.models.base import Base
from app.db.session import async_session, get_db
from datetime import datetime, timedelta
import os
from app.core.config import settings

pytestmark = pytest.mark.asyncio

# 创建测试数据库引擎
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://admin:123456@localhost:5432/multi_tenant_test"
)
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

@pytest.fixture(scope="session")
def event_loop():
    """创建一个事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """设置测试数据库"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture
async def test_db():
    """测试数据库会话"""
    async_session.configure(bind=test_engine)
    async with async_session() as session:
        try:
            yield session
            await session.rollback()
        finally:
            await session.close()

@pytest.fixture
async def test_tenant(test_db: AsyncSession):
    """创建测试租户"""
    from app.models.public import Tenant, TenantStatus
    tenant = Tenant(
        name="Test Tenant",
        schema_name="test_tenant",
        status=TenantStatus.ACTIVE,
        description="Test tenant for testing"
    )
    test_db.add(tenant)
    await test_db.flush()
    await test_db.refresh(tenant)
    return tenant

@pytest.fixture
async def test_user(test_db: AsyncSession, test_tenant):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password="hashed_password",
        is_active=True,
        is_superuser=False,
        tenant_id=test_tenant.id
    )
    test_db.add(user)
    await test_db.flush()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def test_token(test_user: User):
    """创建测试用户的访问令牌"""
    return create_access_token({"sub": test_user.username})

@pytest.fixture
def client(test_db: AsyncSession):
    """测试客户端"""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(test_user: User):
    """创建认证头信息"""
    access_token = create_access_token(
        data={"sub": test_user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.asyncio
async def test_access_log_middleware(client: TestClient):
    # 使用一个已知存在的端点
    response = client.get("/api/v1/user/list", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == 200
    
    # 验证访问日志是否被创建
    async with AsyncSession(test_engine) as session:
        result = await session.execute(
            "SELECT * FROM access_logs WHERE path = '/api/v1/user/list'"
        )
        log = result.fetchone()
        assert log is not None
        assert log.method == "GET"
        assert log.status_code == 200

@pytest.mark.asyncio
async def test_audit_log_user_operations(client: TestClient, auth_headers: dict):
    # 创建新用户
    new_user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "is_active": True,
        "is_superuser": False,
        "user_type": "normal"
    }
    response = client.post(
        "/api/v1/user/create",
        json=new_user_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # 验证审计日志是否被创建
    async with AsyncSession(test_engine) as session:
        result = await session.execute(
            "SELECT * FROM audit_logs WHERE action = 'create' AND resource_type = 'user'"
        )
        log = result.fetchone()
        assert log is not None
        assert log.details == f"Created new user: {new_user_data['username']}"

@pytest.mark.asyncio
async def test_log_query_api(client: TestClient, auth_headers: dict):
    # 查询访问日志
    response = client.get(
        "/api/v1/logs/access",
        params={"page": 1, "page_size": 10},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    
    # 查询审计日志
    response = client.get(
        "/api/v1/logs/audit",
        params={"page": 1, "page_size": 10},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data