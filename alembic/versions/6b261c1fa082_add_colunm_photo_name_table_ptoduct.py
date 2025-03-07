"""add_colunm_photo_name_table_ptoduct

Revision ID: 6b261c1fa082
Revises: 8b557ae08692
Create Date: 2025-03-07 17:08:17.864329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b261c1fa082'
down_revision: Union[str, None] = '8b557ae08692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('photo_name', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'photo_name')
    # ### end Alembic commands ###
