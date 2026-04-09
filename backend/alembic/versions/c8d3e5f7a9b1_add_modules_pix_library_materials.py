"""add modules: pix, library, class_materials, installment_plans, ticket media

Revision ID: c8d3e5f7a9b1
Revises: b7e2a9f3c1d8
Create Date: 2026-04-06 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8d3e5f7a9b1"
down_revision: Union[str, None] = "b7e2a9f3c1d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── InstallmentPlan table ────────────────────────────────────────────────
    op.create_table(
        "installment_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("original_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("num_installments", sa.Integer, nullable=False),
        sa.Column("interest_rate", sa.Numeric(5, 4), server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("negotiation_reason", sa.Text),
        sa.Column("negotiated_by", sa.String(50)),
        sa.Column("original_boleto_ids", postgresql.JSONB, server_default="[]"),
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
    )

    # ── Boleto: add PIX + installment columns ────────────────────────────────
    op.add_column("boletos", sa.Column("pix_code", sa.Text))
    op.add_column("boletos", sa.Column("pix_txid", sa.String(100)))
    op.add_column("boletos", sa.Column("pix_expiration", sa.Date))
    op.add_column(
        "boletos",
        sa.Column(
            "installment_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("installment_plans.id"),
        ),
    )
    op.add_column("boletos", sa.Column("installment_number", sa.Integer))
    op.create_index("ix_boletos_pix_txid", "boletos", ["pix_txid"])
    op.create_index("ix_boletos_installment_plan_id", "boletos", ["installment_plan_id"])

    # ── Ticket: add media_urls ───────────────────────────────────────────────
    op.add_column(
        "tickets", sa.Column("media_urls", postgresql.JSONB, server_default="[]")
    )

    # ── Books table ──────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("isbn", sa.String(20), index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(500), nullable=False),
        sa.Column("publisher", sa.String(255)),
        sa.Column("year", sa.Integer),
        sa.Column("category", sa.String(100)),
        sa.Column("total_copies", sa.Integer, server_default="1"),
        sa.Column("available_copies", sa.Integer, server_default="1"),
        sa.Column("location", sa.String(50)),
        sa.Column("cover_url", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
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
    )

    # ── Loans table ──────────────────────────────────────────────────────────
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("loan_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("return_date", sa.Date),
        sa.Column("renewals", sa.Integer, server_default="0"),
        sa.Column("max_renewals", sa.Integer, server_default="2"),
        sa.Column("status", sa.String(20), server_default="active"),
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
    )

    # ── ClassMaterials table ─────────────────────────────────────────────────
    op.create_table(
        "class_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "teacher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject_code", sa.String(50), index=True),
        sa.Column("subject_name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("file_type", sa.String(20), server_default="pdf"),
        sa.Column("extracted_text", sa.Text),
        sa.Column("academic_period", sa.String(20), nullable=False),
        sa.Column("upload_date", sa.Date),
        sa.Column("is_active", sa.Boolean, server_default="true"),
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
    )


def downgrade() -> None:
    op.drop_table("class_materials")
    op.drop_table("loans")
    op.drop_table("books")

    op.drop_column("tickets", "media_urls")

    op.drop_index("ix_boletos_installment_plan_id", table_name="boletos")
    op.drop_index("ix_boletos_pix_txid", table_name="boletos")
    op.drop_column("boletos", "installment_number")
    op.drop_column("boletos", "installment_plan_id")
    op.drop_column("boletos", "pix_expiration")
    op.drop_column("boletos", "pix_txid")
    op.drop_column("boletos", "pix_code")

    op.drop_table("installment_plans")
