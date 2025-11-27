"""Add version_code to article_versions table

Revision ID: 20251126_02
Revises: 20251126_01
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251126_02'
down_revision = '20251126_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add version_code column to article_versions table
    op.add_column('article_versions', 
                  sa.Column('version_code', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove version_code column
    op.drop_column('article_versions', 'version_code')
