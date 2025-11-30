"""Add rejected status to ArticleStatus enum

Revision ID: 20251129_02
Revises: 20251129_01
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251129_02'
down_revision = '20251129_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'rejected' value to articlestatus enum
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values easily; no-op downgrade
    pass
