"""update timestamp fields

Revision ID: update_timestamp_fields
Revises: update_user_department
Create Date: 2024-03-24 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'update_timestamp_fields'
down_revision: Union[str, None] = 'update_user_department'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 更新 users 表的时间戳字段
    op.alter_column('users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    op.alter_column('users', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=text('CURRENT_TIMESTAMP'),
        postgresql_onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    
    # 2. 更新 access_logs 表
    # 2.1 先为 NULL 值设置默认值
    op.execute(text("""
        UPDATE access_logs 
        SET created_at = CURRENT_TIMESTAMP 
        WHERE created_at IS NULL
    """))
    
    # 2.2 然后设置 NOT NULL 约束和默认值
    op.alter_column('access_logs', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    
    # 2.3 添加 process_time 字段
    op.add_column('access_logs', sa.Column('process_time', sa.Integer(), nullable=True))

def downgrade() -> None:
    # 1. 恢复 users 表的时间戳字段
    op.alter_column('users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=True
    )
    op.alter_column('users', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        postgresql_onupdate=None,
        nullable=True
    )
    
    # 2. 恢复 access_logs 表
    op.alter_column('access_logs', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=True
    )
    op.drop_column('access_logs', 'process_time') 