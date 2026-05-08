"""add integration_sync_logs table

Revision ID: k7g8h9i0j1k2
Revises: j6f7a8b9c0d1
Create Date: 2026-05-08 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "k7g8h9i0j1k2"
down_revision = "j6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("records_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("students_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("students_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("employees_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("employees_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("errors", postgresql.JSONB(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_sync_logs_integration_id", "integration_sync_logs", ["integration_id"])
    op.create_index("ix_sync_logs_tenant_started", "integration_sync_logs", ["tenant_id", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_sync_logs_tenant_started", table_name="integration_sync_logs")
    op.drop_index("ix_sync_logs_integration_id", table_name="integration_sync_logs")
    op.drop_table("integration_sync_logs")
