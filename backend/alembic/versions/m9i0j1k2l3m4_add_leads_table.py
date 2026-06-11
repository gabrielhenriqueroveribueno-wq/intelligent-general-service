"""add leads table

Revision ID: m9i0j1k2l3m4
Revises: l8h9i0j1k2l3
Create Date: 2026-05-14

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "m9i0j1k2l3m4"
down_revision = "l8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        # index=True aqui duplicaria o op.create_index("ix_leads_email") abaixo
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("institution", sa.String(255)),
        sa.Column("role", sa.String(100)),
        sa.Column("message", sa.Text),
        sa.Column("source", sa.String(50), server_default="landing"),
        sa.Column("utm_source", sa.String(100)),
        sa.Column("utm_medium", sa.String(100)),
        sa.Column("utm_campaign", sa.String(100)),
        sa.Column("extra", postgresql.JSONB, server_default="{}"),
        sa.Column("contacted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_leads_email", "leads", ["email"])


def downgrade() -> None:
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
