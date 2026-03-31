"""add_card_examples_table

Revision ID: 2cf9edf5e618
Revises:
Create Date: 2026-03-30 16:53:12.902001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2cf9edf5e618'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('card_examples',
        sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column('card_id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['flashcards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_card_examples_card_id', 'card_examples', ['card_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_card_examples_card_id', table_name='card_examples')
    op.drop_table('card_examples')
