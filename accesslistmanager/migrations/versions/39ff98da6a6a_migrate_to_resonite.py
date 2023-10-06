"""Migrate to resonite

Revision ID: 39ff98da6a6a
Revises: 8ac0b196f5dd
Create Date: 2023-10-05 07:00:07.688215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39ff98da6a6a'
down_revision: Union[str, None] = '8ac0b196f5dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('neos_user', 'resonite_user')
    with op.batch_alter_table('resonite_user', schema=None) as batch_op:
        batch_op.alter_column('neos_username', new_column_name='resonite_username', nullable=False, unique=True)

def downgrade() -> None:
    op.rename_table('resonite_user', 'neos_user')
    with op.batch_alter_table('neos_user', schema=None) as batch_op:
        batch_op.alter_column('resonite_username', new_column_name='neos_username', nullable=False, unique=True)
