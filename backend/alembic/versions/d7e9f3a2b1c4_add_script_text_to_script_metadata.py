"""add script_text to script_metadata

Revision ID: d7e9f3a2b1c4
Revises: c4d9a8f1e2b3
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'd7e9f3a2b1c4'
down_revision = 'c4d9a8f1e2b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('script_metadata', sa.Column('script_text', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('script_metadata', 'script_text')
