"""add academic integrations

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-04-27 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "academic_integrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "sync_cron",
            sa.String(50),
            nullable=False,
            server_default="0 */6 * * *",
        ),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_duration_ms", sa.Integer(), nullable=True),
        sa.Column("last_sync_records_synced", sa.Integer(), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "provider_type",
            name="uq_integration_tenant_provider",
        ),
        sa.CheckConstraint(
            "provider_type IN ('sophia', 'totvs', 'generic_rest')",
            name="ck_integration_provider_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'paused', 'error')",
            name="ck_integration_status",
        ),
    )

    op.create_index(
        "ix_academic_integrations_status",
        "academic_integrations",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_academic_integrations_status",
        table_name="academic_integrations",
    )
    op.drop_table("academic_integrations")
