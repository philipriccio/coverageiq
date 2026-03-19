"""add mandate checklist to coverage reports

Revision ID: c4d9a8f1e2b3
Revises: b6f6b7d9f2a1
Create Date: 2026-03-19 10:58:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c4d9a8f1e2b3'
down_revision: Union[str, Sequence[str], None] = 'b6f6b7d9f2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('coverage_reports', sa.Column('mandate_checklist', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('coverage_reports', 'mandate_checklist')
