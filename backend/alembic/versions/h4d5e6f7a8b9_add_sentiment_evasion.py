"""add sentiment and evasion risk

Revision ID: h4d5e6f7a8b9
Revises: g3c4d5e6f7a8
Create Date: 2026-04-28 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "h4d5e6f7a8b9"
down_revision: Union[str, None] = "g3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sentimento por mensagem
    op.add_column("messages", sa.Column("sentiment", sa.String(20), nullable=True))
    op.add_column("messages", sa.Column("sentiment_score", sa.Numeric(4, 3), nullable=True))
    op.create_index("ix_messages_sentiment", "messages", ["sentiment"])

    # Risco de evasão por aluno
    op.add_column("students", sa.Column("evasion_risk_score", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("students", sa.Column("evasion_risk_level", sa.String(20), nullable=True, server_default="low"))
    op.add_column("students", sa.Column("evasion_risk_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("students", sa.Column("evasion_factors", sa.Text(), nullable=True))
    op.create_index("ix_students_evasion_risk_level", "students", ["evasion_risk_level"])


def downgrade() -> None:
    op.drop_index("ix_students_evasion_risk_level", "students")
    op.drop_column("students", "evasion_factors")
    op.drop_column("students", "evasion_risk_updated_at")
    op.drop_column("students", "evasion_risk_level")
    op.drop_column("students", "evasion_risk_score")
    op.drop_index("ix_messages_sentiment", "messages")
    op.drop_column("messages", "sentiment_score")
    op.drop_column("messages", "sentiment")
