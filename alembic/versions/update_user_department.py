"""update user department

Revision ID: update_user_department
Revises: ab7d744ed557
Create Date: 2024-03-24 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'update_user_department'
down_revision: Union[str, None] = 'ab7d744ed557'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 添加新的 department 字段
    op.add_column('users', sa.Column('department', sa.String(100), nullable=True))
    
    # 2. 删除旧的 dept_id 字段
    op.drop_column('users', 'dept_id')

def downgrade() -> None:
    # 1. 添加回 dept_id 字段
    op.add_column('users', sa.Column('dept_id', sa.Integer(), nullable=True))
    
    # 2. 删除 department 字段
    op.drop_column('users', 'department') 