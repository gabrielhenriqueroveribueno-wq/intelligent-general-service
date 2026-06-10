"""make audit_logs.tenant_id nullable for platform-level actions

Revision ID: n0j1k2l3m4n5
Revises: m9i0j1k2l3m4
Create Date: 2026-06-10

Platform-level actions (super_admin without a tenant) such as login_success
must be auditable even without a tenant_id. The NOT NULL constraint inherited
from TenantMixin broke super_admin login when the audit insert was committed.
"""
from alembic import op

revision = "n0j1k2l3m4n5"
down_revision = "m9i0j1k2l3m4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("audit_logs", "tenant_id", nullable=True)


def downgrade() -> None:
    op.alter_column("audit_logs", "tenant_id", nullable=False)
