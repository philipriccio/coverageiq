"""Add examples, domain knowledge, and OpenAI defaults

Revision ID: b6f6b7d9f2a1
Revises: 8562ca56853a
Create Date: 2026-03-18 20:20:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b6f6b7d9f2a1'
down_revision: Union[str, Sequence[str], None] = '8562ca56853a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'domain_knowledge',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_domain_knowledge_category'), 'domain_knowledge', ['category'], unique=False)

    op.create_table(
        'coverage_examples',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('script_title', sa.String(length=500), nullable=False),
        sa.Column('genre', sa.String(length=100), nullable=True),
        sa.Column('analysis_depth', sa.String(length=20), nullable=False),
        sa.Column('coverage_report_id', sa.String(length=36), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['coverage_report_id'], ['coverage_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('coverage_report_id')
    )
    op.create_index(op.f('ix_coverage_examples_genre'), 'coverage_examples', ['genre'], unique=False)

    op.execute("UPDATE coverage_reports SET model_used = 'gpt-4.1' WHERE model_used LIKE 'kimi%' OR model_used LIKE 'moonshot%'")


def downgrade() -> None:
    op.drop_index(op.f('ix_coverage_examples_genre'), table_name='coverage_examples')
    op.drop_table('coverage_examples')
    op.drop_index(op.f('ix_domain_knowledge_category'), table_name='domain_knowledge')
    op.drop_table('domain_knowledge')
