"""add appointments table

Revision ID: d9e4f6a7b2c3
Revises: c8d3e5f7a9b1
Create Date: 2026-04-10 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9e4f6a7b2c3"
down_revision: Union[str, None] = "c8d3e5f7a9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    appointment_status = postgresql.ENUM(
        "scheduled", "confirmed", "cancelled", "completed", "no_show",
        name="appointment_status",
        create_type=False,
    )
    appointment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False, index=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_time", sa.Time(), nullable=False),
        sa.Column("department", sa.String(100), nullable=False, server_default="secretaria"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", appointment_status, nullable=False, server_default="scheduled"),
        sa.Column("protocol", sa.String(30), nullable=False, unique=True, index=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Index for querying available slots
    op.create_index(
        "ix_appointments_date_dept",
        "appointments",
        ["tenant_id", "appointment_date", "department", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_date_dept", table_name="appointments")
    op.drop_table("appointments")
    op.execute("DROP TYPE IF EXISTS appointment_status")
