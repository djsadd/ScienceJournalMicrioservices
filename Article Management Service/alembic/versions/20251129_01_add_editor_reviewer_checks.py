"""Add editor_check and reviewer_check to ArticleStatus enum

Revision ID: 20251129_01
Revises: f02b17fc7620
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251129_01'
down_revision = 'f02b17fc7620'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to articlestatus enum if not present
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'editor_check'")
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'reviewer_check'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values easily; no-op downgrade
    pass
