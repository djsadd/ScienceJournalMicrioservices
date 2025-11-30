"""Add volumes and volume_articles tables

Revision ID: 20251130_01
Revises: 20251129_02
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251130_01'
down_revision = '20251129_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'volumes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title_kz', sa.String(), nullable=True),
        sa.Column('title_en', sa.String(), nullable=True),
        sa.Column('title_ru', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.UniqueConstraint('year', 'number', name='uq_volumes_year_number'),
    )

    op.create_table(
        'volume_articles',
        sa.Column('volume_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['volume_id'], ['volumes.id']),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id']),
        sa.PrimaryKeyConstraint('volume_id', 'article_id'),
    )


def downgrade() -> None:
    op.drop_table('volume_articles')
    op.drop_table('volumes')
