"""Add performance indexes for conversations, messages, students, tickets

Revision ID: i5e6f7a8b9c0
Revises: h4d5e6f7a8b9
Create Date: 2026-04-28
"""

from alembic import op

revision = "i5e6f7a8b9c0"
down_revision = "h4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Conversations ────────────────────────────────────────────────────────
    # Lista de conversas por tenant filtrada por status (query mais comum)
    op.create_index(
        "ix_conversations_tenant_status",
        "conversations",
        ["tenant_id", "status"],
        if_not_exists=True,
    )
    # Ordenação por última mensagem (padrão da listagem)
    op.create_index(
        "ix_conversations_tenant_last_msg",
        "conversations",
        ["tenant_id", "last_message_at"],
        if_not_exists=True,
    )
    # Conversas atribuídas a um agente específico
    op.create_index(
        "ix_conversations_assigned_agent",
        "conversations",
        ["assigned_agent_id"],
        if_not_exists=True,
    )

    # ── Messages ─────────────────────────────────────────────────────────────
    # Busca de mensagens por conversa + data (paginação)
    op.create_index(
        "ix_messages_conv_created",
        "messages",
        ["conversation_id", "created_at"],
        if_not_exists=True,
    )
    # Busca por sender_type (filtragem de mensagens de usuário para análise)
    op.create_index(
        "ix_messages_sender_type",
        "messages",
        ["conversation_id", "sender_type"],
        if_not_exists=True,
    )

    # ── Students ─────────────────────────────────────────────────────────────
    # Filtro por tenant + status de matrícula (mais usados)
    op.create_index(
        "ix_students_tenant_enrollment",
        "students",
        ["tenant_id", "enrollment_status"],
        if_not_exists=True,
    )
    # Busca por nome (LIKE) — partial index seria ideal mas Alembic básico não suporta
    op.create_index(
        "ix_students_name",
        "students",
        ["tenant_id", "full_name"],
        if_not_exists=True,
    )

    # ── Tickets ──────────────────────────────────────────────────────────────
    # Lista de tickets por tenant + status + prioridade
    op.create_index(
        "ix_tickets_tenant_status_priority",
        "tickets",
        ["tenant_id", "status", "priority"],
        if_not_exists=True,
    )
    # SLA check — tickets abertos com prazo próximo
    op.create_index(
        "ix_tickets_due_date",
        "tickets",
        ["due_date", "status"],
        if_not_exists=True,
    )

    # ── Boletos ──────────────────────────────────────────────────────────────
    # Boletos vencidos para lembretes
    op.create_index(
        "ix_boletos_tenant_status_due",
        "boletos",
        ["tenant_id", "status", "due_date"],
        if_not_exists=True,
    )

    # ── Audit logs ───────────────────────────────────────────────────────────
    op.create_index(
        "ix_audit_logs_tenant_created",
        "audit_logs",
        ["tenant_id", "created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_tenant_created", table_name="audit_logs")
    op.drop_index("ix_boletos_tenant_status_due", table_name="boletos")
    op.drop_index("ix_tickets_due_date", table_name="tickets")
    op.drop_index("ix_tickets_tenant_status_priority", table_name="tickets")
    op.drop_index("ix_students_name", table_name="students")
    op.drop_index("ix_students_tenant_enrollment", table_name="students")
    op.drop_index("ix_messages_sender_type", table_name="messages")
    op.drop_index("ix_messages_conv_created", table_name="messages")
    op.drop_index("ix_conversations_assigned_agent", table_name="conversations")
    op.drop_index("ix_conversations_tenant_last_msg", table_name="conversations")
    op.drop_index("ix_conversations_tenant_status", table_name="conversations")
