"""Change volume number type from INTEGER to VARCHAR

Revision ID: 20260128_01
Revises: 20251130_04
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260128_01'
down_revision = '20251130_04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change the type of number column from INTEGER to VARCHAR
    op.alter_column('volumes', 'number', type_=sa.String(), existing_type=sa.Integer())


def downgrade() -> None:
    # Revert back to INTEGER (this will fail if there are non-numeric values)
    op.alter_column('volumes', 'number', type_=sa.Integer(), existing_type=sa.String())
