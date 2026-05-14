"""drop slide tables (tech debt cleanup)

Revision ID: l8h9i0j1k2l3
Revises: k7g8h9i0j1k2
Create Date: 2026-05-12 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "l8h9i0j1k2l3"
down_revision = "k7g8h9i0j1k2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # slide_generation_logs references slide_presentations → drop logs first
    op.drop_table("slide_generation_logs")
    op.drop_table("slide_presentations")
    op.drop_table("slide_templates")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "slide_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("template_rules", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("example_content", sa.Text, nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "slide_presentations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("prompt_used", sa.Text, nullable=False),
        sa.Column("slides_content", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("total_slides", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["template_id"], ["slide_templates.id"]),
    )
    op.create_table(
        "slide_generation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("presentation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ai_provider", sa.String(30), nullable=False, server_default="groq"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["presentation_id"], ["slide_presentations.id"]),
    )
