"""Add withdrawn status to ArticleStatus enum

Revision ID: 20251126_01
Revises: 
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251126_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'withdrawn' value to articlestatus enum
    op.execute("ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'withdrawn'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type if you want to remove a value
    pass
