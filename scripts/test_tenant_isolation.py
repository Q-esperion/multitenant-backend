import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.public import User, Tenant, UserRole, Role
from app.schemas.tenant import TenantCreate
from app.core.security import encrypt_password

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.token = None
        self.headers = {}

    async def login(self, username: str, password: str) -> Dict:
        """登录获取token"""
        try:
            # 准备请求数据
            request_data = {
                "username": username,
                "password": encrypt_password(password)
            }
            logger.info(f"登录请求数据: {request_data}")
            
            # 发送请求
            response = await self.client.post(
                "/api/v1/base/access_token",
                json=request_data
            )
            
            # 记录响应状态和内容
            logger.info(f"登录响应状态码: {response.status_code}")
            logger.info(f"登录响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            self.token = data["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.info(f"用户 {username} 登录成功")
            return data
        except Exception as e:
            logger.error(f"用户 {username} 登录失败: {str(e)}")
            raise

    async def create_tenant(self, tenant_data: Dict) -> Dict:
        """创建租户"""
        try:
            response = await self.client.post(
                "/api/v1/tenant/create",
                json=tenant_data,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"创建租户成功: {tenant_data['name']}")
            return data
        except Exception as e:
            logger.error(f"创建租户失败: {str(e)}")
            raise

    async def create_user(self, user_data: Dict) -> Dict:
        """创建用户"""
        try:
            # 确保密码已加密
            if not user_data.get("password"):
                raise ValueError("密码不能为空")
            
            logger.info(f"创建用户请求数据: {user_data}")
            response = await self.client.post(
                "/api/v1/user/create",
                json=user_data,
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"创建用户失败，状态码: {response.status_code}")
                logger.error(f"错误响应: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"创建用户成功: {user_data['username']}")
            return data
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            raise

    async def insert_student(self, tenant_id: int, student_data: Dict) -> Dict:
        """向指定租户插入学生数据"""
        try:
            # 检查当前用户是否有权限操作该租户的数据
            if not self.token:
                raise Exception("未登录")
            
            # 获取当前用户信息
            response = await self.client.get(
                "/api/v1/base/userinfo",
                headers=self.headers
            )
            response.raise_for_status()
            current_user = response.json()["data"]
            logger.info(f"当前用户信息: {current_user}")
            
            # 权限校验
            if current_user.get("is_superuser"):
                # 超级管理员可以操作所有租户的数据
                logger.info("用户是超级管理员，允许操作")
                pass
            elif current_user.get("is_tenant_admin") and current_user.get("tenant_id") == tenant_id:
                # 租户管理员只能操作自己租户的数据
                logger.info("用户是租户管理员且操作自己的租户，允许操作")
                pass
            else:
                logger.error(f"权限校验失败: tenant_id={current_user.get('tenant_id')}, target_tenant_id={tenant_id}, is_tenant_admin={current_user.get('is_tenant_admin')}")
                raise Exception("没有权限操作该租户的数据")
            
            # 将 birth_date 字符串转换为 date 对象
            if isinstance(student_data.get('birth_date'), str):
                student_data['birth_date'] = datetime.strptime(student_data['birth_date'], '%Y-%m-%d').date()
            
            # 切换到租户schema
            async with AsyncSessionLocal() as session:
                await session.execute(text(f"SET search_path TO tenant_{tenant_id}"))
                await session.execute(
                    text("""
                        INSERT INTO students (id_card, student_id, name, gender, birth_date, department_id)
                        VALUES (:id_card, :student_id, :name, :gender, :birth_date, :department_id)
                    """),
                    student_data
                )
                await session.commit()
            logger.info(f"向租户 {tenant_id} 插入学生数据成功: {student_data['name']}")
            return {"success": True}
        except Exception as e:
            logger.error(f"插入学生数据失败: {str(e)}")
            raise

async def init_test_data():
    """初始化测试数据"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在系统管理员角色
        result = await session.execute(
            text("SELECT id FROM roles WHERE code = 'admin'")
        )
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            # 创建超级管理员角色
            admin_role = Role(
                name="系统管理员",
                code="admin",
                description="系统管理员角色"
            )
            session.add(admin_role)
            await session.commit()
            logger.info("创建系统管理员角色成功")
        else:
            logger.info("系统管理员角色已存在")
        
        # 检查是否已存在超级管理员用户
        result = await session.execute(
            text("SELECT id FROM users WHERE username = 'admin'")
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            # 创建超级管理员用户
            admin_user = User(
                username="admin",
                password=encrypt_password("Admin@123456"),
                email="admin@example.com",
                is_active=True,
                is_superuser=True
            )
            session.add(admin_user)
            await session.commit()
            logger.info("创建超级管理员用户成功")
            
            # 为超级管理员分配角色
            await session.execute(
                text("""
                    INSERT INTO user_roles (user_id, role_id)
                    SELECT :user_id, id FROM roles WHERE code = 'admin'
                """),
                {"user_id": admin_user.id}
            )
            await session.commit()
            logger.info("为超级管理员分配角色成功")
        else:
            logger.info("超级管理员用户已存在")

async def main():
    """主测试流程"""
    logger.info("开始测试租户数据隔离和权限管控功能")
    
    # 初始化测试数据
    await init_test_data()
    
    # 创建测试客户端
    client = TestClient()
    
    # 超级管理员登录
    await client.login("admin", "Admin@123456")
    
    # 创建租户
    tenant_aa = await client.create_tenant({
        "name": "AA租户",
        "description": "AA租户描述",
        "max_users": 100,
        "expire_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    })
    
    tenant_bb = await client.create_tenant({
        "name": "BB租户",
        "description": "BB租户描述",
        "max_users": 100,
        "expire_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    })
    
    # 创建用户
    user_a = await client.create_user({
        "username": "user_a",
        "password": encrypt_password("Password123!"),
        "email": "user_a@example.com",
        "phone": "13800138000",
        "tenant_id": tenant_aa["data"]["id"],
        "is_active": True,
        "is_tenant_admin": True,
        "role_ids": []
    })
    
    user_b = await client.create_user({
        "username": "user_b",
        "password": encrypt_password("Password123!"),
        "email": "user_b@example.com",
        "phone": "13800138001",
        "tenant_id": tenant_bb["data"]["id"],
        "is_active": True,
        "is_tenant_admin": True,
        "role_ids": []
    })
    
    user_c = await client.create_user({
        "username": "user_c",
        "password": encrypt_password("Password123!"),
        "email": "user_c@example.com",
        "phone": "13800138002",
        "tenant_id": tenant_aa["data"]["id"],
        "is_active": True,
        "is_tenant_admin": False,
        "role_ids": []
    })
    
    # 设置租户管理员
    async with AsyncSessionLocal() as session:
        # 为user_a设置AA租户管理员角色
        await session.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT :user_id, id FROM roles WHERE code = 'tenant_admin'
            """),
            {"user_id": user_a["data"]["id"]}
        )
        
        # 为user_b设置BB租户管理员角色
        await session.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT :user_id, id FROM roles WHERE code = 'tenant_admin'
            """),
            {"user_id": user_b["data"]["id"]}
        )
        
        await session.commit()
        logger.info("设置租户管理员成功")
    
    # 使用不同用户插入数据
    # 用户A插入AA租户数据
    await client.login("user_a", "Password123!")
    await client.insert_student(tenant_aa["data"]["id"], {
        "id_card": "110101199001011234",
        "student_id": "AA001",
        "name": "AA学生1",
        "gender": "男",
        "birth_date": "1990-01-01",
        "department_id": 1
    })
    
    # 用户B插入BB租户数据
    await client.login("user_b", "Password123!")
    await client.insert_student(tenant_bb["data"]["id"], {
        "id_card": "110101199001011235",
        "student_id": "BB001",
        "name": "BB学生1",
        "gender": "女",
        "birth_date": "1990-01-02",
        "department_id": 1
    })
    
    # 用户C尝试插入AA租户数据（应该失败）
    await client.login("user_c", "Password123!")
    try:
        await client.insert_student(tenant_aa["data"]["id"], {
            "id_card": "110101199001011236",
            "student_id": "AA002",
            "name": "AA学生2",
            "gender": "男",
            "birth_date": "1990-01-03",
            "department_id": 1
        })
    except Exception as e:
        logger.info(f"用户C插入数据失败（符合预期）: {str(e)}")
    
    # 验证数据隔离
    async with AsyncSessionLocal() as session:
        # 检查AA租户数据
        await session.execute(text(f"SET search_path TO tenant_{tenant_aa['data']['id']}"))
        result = await session.execute(text("SELECT * FROM students"))
        aa_students = result.fetchall()
        logger.info(f"AA租户学生数据: {aa_students}")
        
        # 检查BB租户数据
        await session.execute(text(f"SET search_path TO tenant_{tenant_bb['data']['id']}"))
        result = await session.execute(text("SELECT * FROM students"))
        bb_students = result.fetchall()
        logger.info(f"BB租户学生数据: {bb_students}")
    
    logger.info("测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 