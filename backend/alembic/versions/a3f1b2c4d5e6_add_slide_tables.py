"""add slide_templates, slide_presentations, slide_generation_logs tables

Revision ID: a3f1b2c4d5e6
Revises: 84781b46eefb
Create Date: 2026-03-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3f1b2c4d5e6'
down_revision: Union[str, None] = '84781b46eefb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # slide_templates
    op.create_table('slide_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('example_content', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slide_templates_tenant_id'), 'slide_templates', ['tenant_id'], unique=False)

    # slide_presentations
    op.create_table('slide_presentations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('prompt_used', sa.Text(), nullable=False),
        sa.Column('slides_content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('total_slides', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id']),
        sa.ForeignKeyConstraint(['template_id'], ['slide_templates.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slide_presentations_tenant_id'), 'slide_presentations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slide_presentations_teacher_id'), 'slide_presentations', ['teacher_id'], unique=False)

    # slide_generation_logs
    op.create_table('slide_generation_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('presentation_id', sa.UUID(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('ai_provider', sa.String(length=30), nullable=False, server_default=sa.text("'groq'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id']),
        sa.ForeignKeyConstraint(['presentation_id'], ['slide_presentations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slide_generation_logs_tenant_id'), 'slide_generation_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slide_generation_logs_teacher_id'), 'slide_generation_logs', ['teacher_id'], unique=False)
    op.create_index(op.f('ix_slide_generation_logs_presentation_id'), 'slide_generation_logs', ['presentation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_slide_generation_logs_presentation_id'), table_name='slide_generation_logs')
    op.drop_index(op.f('ix_slide_generation_logs_teacher_id'), table_name='slide_generation_logs')
    op.drop_index(op.f('ix_slide_generation_logs_tenant_id'), table_name='slide_generation_logs')
    op.drop_table('slide_generation_logs')

    op.drop_index(op.f('ix_slide_presentations_teacher_id'), table_name='slide_presentations')
    op.drop_index(op.f('ix_slide_presentations_tenant_id'), table_name='slide_presentations')
    op.drop_table('slide_presentations')

    op.drop_index(op.f('ix_slide_templates_tenant_id'), table_name='slide_templates')
    op.drop_table('slide_templates')
