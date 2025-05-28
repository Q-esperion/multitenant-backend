"""add_role_visibility_fields

Revision ID: add_role_visibility_fields
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_role_visibility_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 添加 is_superuser_only 字段
    op.add_column('roles', sa.Column('is_superuser_only', sa.Boolean(), nullable=False, server_default='false'))
    
    # 添加 tenant_id 字段
    op.add_column('roles', sa.Column('tenant_id', sa.Integer(), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_roles_tenant_id_tenants',
        'roles', 'tenants',
        ['tenant_id'], ['id']
    )

def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_roles_tenant_id_tenants', 'roles', type_='foreignkey')
    
    # 删除字段
    op.drop_column('roles', 'tenant_id')
    op.drop_column('roles', 'is_superuser_only') 