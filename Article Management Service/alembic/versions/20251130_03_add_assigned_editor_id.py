"""Add assigned_editor_id to articles

Revision ID: 20251130_03
Revises: 20251130_02
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251130_03'
down_revision = '20251130_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('articles', sa.Column('assigned_editor_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('articles', 'assigned_editor_id')
