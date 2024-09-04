"""change filename fields to filepath

Revision ID: e4d95e2df049
Revises: 3fc2149d3f0c
Create Date: 2024-08-26 17:50:38.059914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4d95e2df049'
down_revision: Union[str, None] = '3fc2149d3f0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chains', sa.Column('filepath', sa.String(), nullable=False))
    op.drop_column('chains', 'filename')
    op.add_column('projects', sa.Column('filepath', sa.String(), nullable=False))
    op.drop_column('projects', 'filename')
    op.add_column('quests', sa.Column('filepath', sa.String(), nullable=False))
    op.drop_column('quests', 'filename')
    op.add_column('tasks', sa.Column('filepath', sa.String(), nullable=False))
    op.drop_column('tasks', 'filename')
    op.add_column('users', sa.Column('filepath', sa.String(), nullable=False))
    op.drop_column('users', 'filename')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('users', 'filepath')
    op.add_column('tasks', sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('tasks', 'filepath')
    op.add_column('quests', sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('quests', 'filepath')
    op.add_column('projects', sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('projects', 'filepath')
    op.add_column('chains', sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('chains', 'filepath')
    # ### end Alembic commands ###
