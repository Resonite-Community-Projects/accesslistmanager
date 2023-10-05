"""Initial migation

Revision ID: 8ac0b196f5dd
Revises: 
Create Date: 2023-10-05 06:55:48.508680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ac0b196f5dd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('neos_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('neos_username', sa.Text(), nullable=False),
    sa.Column('discord_id', sa.Text(), nullable=False),
    sa.Column('verifier', sa.Text(), nullable=False),
    sa.Column('verified_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('neos_username')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('neos_user')
    # ### end Alembic commands ###
