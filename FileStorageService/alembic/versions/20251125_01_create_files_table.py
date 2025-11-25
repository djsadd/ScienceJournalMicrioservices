"""create files table

Revision ID: 20251125_01
Revises:
Create Date: 2025-11-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251125_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("original_name", sa.String(), nullable=False),
        sa.Column("stored_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_files_stored_name", "files", ["stored_name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_files_stored_name", table_name="files")
    op.drop_table("files")

