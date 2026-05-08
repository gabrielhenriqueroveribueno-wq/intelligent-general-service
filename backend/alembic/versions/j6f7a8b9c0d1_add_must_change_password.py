"""add must_change_password to users

Revision ID: j6f7a8b9c0d1
Revises: i5e6f7a8b9c0
Create Date: 2026-05-08 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "j6f7a8b9c0d1"
down_revision = "i5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
