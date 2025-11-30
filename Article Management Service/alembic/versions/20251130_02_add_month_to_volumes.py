"""Add month column to volumes

Revision ID: 20251130_02
Revises: 20251130_01
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251130_02'
down_revision = '20251130_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('volumes', sa.Column('month', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('volumes', 'month')
