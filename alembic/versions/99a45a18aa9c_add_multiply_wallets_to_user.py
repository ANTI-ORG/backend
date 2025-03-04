"""add multiply wallets to user

Revision ID: 99a45a18aa9c
Revises: a28d10f0340a
Create Date: 2024-08-22 00:35:55.859001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99a45a18aa9c'
down_revision: Union[str, None] = 'a28d10f0340a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wallets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('web3_address', sa.String(length=100), nullable=False),
    sa.Column('wallet_network', sa.Enum('Ethereum', 'Solana', name='walletnetwork'), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallets_id'), 'wallets', ['id'], unique=False)
    op.create_index(op.f('ix_wallets_web3_address'), 'wallets', ['web3_address'], unique=True)
    op.drop_constraint('quests_project_id_fkey', 'quests', type_='foreignkey')
    op.drop_constraint('quests_chain_id_fkey', 'quests', type_='foreignkey')
    op.create_foreign_key(None, 'quests', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'quests', 'chains', ['chain_id'], ['id'], ondelete='SET NULL')
    op.drop_constraint('tokens_user_id_fkey', 'tokens', type_='foreignkey')
    op.create_foreign_key(None, 'tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('user_ip_ip_address_id_fkey', 'user_ip', type_='foreignkey')
    op.drop_constraint('user_ip_user_id_fkey', 'user_ip', type_='foreignkey')
    op.create_foreign_key(None, 'user_ip', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'user_ip', 'ip_addresses', ['ip_address_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('user_quest_user_id_fkey', 'user_quest', type_='foreignkey')
    op.drop_constraint('user_quest_quest_id_fkey', 'user_quest', type_='foreignkey')
    op.create_foreign_key(None, 'user_quest', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'user_quest', 'quests', ['quest_id'], ['id'], ondelete='CASCADE')
    op.drop_index('ix_users_web3_address', table_name='users')
    op.drop_column('users', 'web3_address')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('web3_address', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.create_index('ix_users_web3_address', 'users', ['web3_address'], unique=True)
    op.drop_constraint(None, 'user_quest', type_='foreignkey')
    op.drop_constraint(None, 'user_quest', type_='foreignkey')
    op.create_foreign_key('user_quest_quest_id_fkey', 'user_quest', 'quests', ['quest_id'], ['id'])
    op.create_foreign_key('user_quest_user_id_fkey', 'user_quest', 'users', ['user_id'], ['id'])
    op.drop_constraint(None, 'user_ip', type_='foreignkey')
    op.drop_constraint(None, 'user_ip', type_='foreignkey')
    op.create_foreign_key('user_ip_user_id_fkey', 'user_ip', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_ip_ip_address_id_fkey', 'user_ip', 'ip_addresses', ['ip_address_id'], ['id'])
    op.drop_constraint(None, 'tokens', type_='foreignkey')
    op.create_foreign_key('tokens_user_id_fkey', 'tokens', 'users', ['user_id'], ['id'])
    op.drop_constraint(None, 'quests', type_='foreignkey')
    op.drop_constraint(None, 'quests', type_='foreignkey')
    op.create_foreign_key('quests_chain_id_fkey', 'quests', 'chains', ['chain_id'], ['id'])
    op.create_foreign_key('quests_project_id_fkey', 'quests', 'projects', ['project_id'], ['id'])
    op.drop_index(op.f('ix_wallets_web3_address'), table_name='wallets')
    op.drop_index(op.f('ix_wallets_id'), table_name='wallets')
    op.drop_table('wallets')
    # ### end Alembic commands ###
