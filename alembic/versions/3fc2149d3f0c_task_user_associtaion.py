"""task user associtaion

Revision ID: 3fc2149d3f0c
Revises: 808d7f808dbb
Create Date: 2024-08-23 13:16:21.796709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fc2149d3f0c'
down_revision: Union[str, None] = '808d7f808dbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_tasks',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'task_id')
    )
    op.add_column('tasks', sa.Column('button_link', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'button_link')
    op.drop_table('user_tasks')
    # ### end Alembic commands ###
