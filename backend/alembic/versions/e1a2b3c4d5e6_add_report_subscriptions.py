"""add report subscriptions

Revision ID: e1a2b3c4d5e6
Revises: d9e4f6a7b2c3
Create Date: 2026-04-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "d9e4f6a7b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_subscriptions",
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
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("period", sa.String(20), nullable=False, server_default="weekly"),
        sa.Column(
            "recipients",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("send_hour_utc", sa.Integer(), nullable=False, server_default=sa.text("11")),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "period IN ('daily', 'weekly', 'monthly')",
            name="ck_report_subscription_period",
        ),
        sa.CheckConstraint(
            "send_hour_utc BETWEEN 0 AND 23",
            name="ck_report_subscription_hour",
        ),
    )

    op.create_index(
        "ix_report_subscriptions_tenant_active",
        "report_subscriptions",
        ["tenant_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_report_subscriptions_tenant_active",
        table_name="report_subscriptions",
    )
    op.drop_table("report_subscriptions")
