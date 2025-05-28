"""make_role_code_nullable

Revision ID: 6c67aed5487b
Revises: add_role_visibility_fields
Create Date: 2025-05-28 15:47:23.508761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c67aed5487b'
down_revision: Union[str, None] = 'add_role_visibility_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 修改 code 字段为可空
    op.alter_column('roles', 'code',
        existing_type=sa.String(50),
        nullable=True,
        existing_unique=True)


def downgrade() -> None:
    # 恢复 code 字段为不可空
    op.alter_column('roles', 'code',
        existing_type=sa.String(50),
        nullable=False,
        existing_unique=True)
