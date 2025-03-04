"""delete nonce field (User)

Revision ID: f8cbb7a43edd
Revises: 273de06ac771
Create Date: 2024-08-18 17:41:09.310206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8cbb7a43edd'
down_revision: Union[str, None] = '273de06ac771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'nonce')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('nonce', sa.VARCHAR(length=16), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
