"""add_colunm_status_table_order

Revision ID: 0b7f261c1cc8
Revises: 6b261c1fa082
Create Date: 2025-03-12 15:54:56.016400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b7f261c1cc8'
down_revision: Union[str, None] = '6b261c1fa082'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

order_status_enum = sa.Enum('processing', 'completed', name='orderstatus')

def upgrade() -> None:
    # Создаём ENUM-тип в БД
    order_status_enum.create(op.get_bind(), checkfirst=True)

    # Добавляем колонку после создания ENUM
    op.add_column('order', sa.Column('status', order_status_enum, nullable=False, server_default='processing'))

def downgrade() -> None:
    # Удаляем колонку
    op.drop_column('order', 'status')

    # Удаляем ENUM-тип (если он больше нигде не используется)
    order_status_enum.drop(op.get_bind(), checkfirst=True)
