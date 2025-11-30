"""Add sent_for_revision to ArticleStatus enum

Revision ID: 20251130_04
Revises: 20251130_03
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251130_04'
# Depends on previous migration that added assigned_editor_id
down_revision = '20251130_03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new value to articlestatus enum if not present
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'sent_for_revision'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values easily; leaving as no-op
    pass
