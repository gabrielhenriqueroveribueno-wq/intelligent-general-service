import csv
import io
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.ticket import Ticket


async def get_conversation_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    result = await db.execute(
        select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= start_date,
            Conversation.started_at <= end_date,
        ).order_by(Conversation.started_at.desc())
    )
    conversations = result.scalars().all()

    rows = []
    for conv in conversations:
        rows.append(
            {
                "id": str(conv.id),
                "status": conv.status,
                "context_type": conv.context_type or "",
                "started_at": conv.started_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else "",
                "satisfaction_score": conv.satisfaction_score or "",
            }
        )
    return rows


async def get_ticket_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    result = await db.execute(
        select(Ticket).where(
            Ticket.tenant_id == tenant_id,
            Ticket.created_at >= start_date,
            Ticket.created_at <= end_date,
        ).order_by(Ticket.created_at.desc())
    )
    tickets = result.scalars().all()

    rows = []
    for t in tickets:
        rows.append(
            {
                "protocol": t.protocol_number,
                "subject": t.subject,
                "category": t.category or "",
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else "",
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else "",
            }
        )
    return rows


def rows_to_csv(rows: list[dict]) -> bytes:
    """Converte lista de dicts para CSV em bytes."""
    if not rows:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")  # BOM para Excel


async def get_dashboard_overview(
    db: AsyncSession, tenant_id: uuid.UUID
) -> dict:
    from datetime import timezone, timedelta

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Conversas hoje
    r1 = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= today_start,
        )
    )
    today_convs = r1.scalar() or 0

    # Conversas semana
    r2 = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= week_start,
        )
    )
    week_convs = r2.scalar() or 0

    # Conversas mês
    r3 = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= month_start,
        )
    )
    month_convs = r3.scalar() or 0

    # Tickets abertos
    r4 = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == tenant_id,
            Ticket.status.in_(["open", "in_progress"]),
        )
    )
    open_tickets = r4.scalar() or 0

    # Tickets com SLA violado
    r5 = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == tenant_id,
            Ticket.status.in_(["open", "in_progress"]),
            Ticket.sla_deadline < now,
        )
    )
    sla_breached = r5.scalar() or 0

    # Taxa de resolução automática (mensagens com sender_type=bot / total)
    r6 = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.status == "closed",
            Conversation.started_at >= month_start,
        )
    )
    closed = r6.scalar() or 0

    r7 = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.status == "closed",
            Conversation.assigned_agent_id.is_(None),
            Conversation.started_at >= month_start,
        )
    )
    auto_closed = r7.scalar() or 0

    auto_rate = (auto_closed / closed * 100) if closed > 0 else 0.0

    return {
        "total_conversations_today": today_convs,
        "total_conversations_week": week_convs,
        "total_conversations_month": month_convs,
        "auto_resolution_rate": round(auto_rate, 1),
        "avg_response_time_seconds": 0.0,  # calculado via Prometheus
        "open_tickets": open_tickets,
        "sla_breached_tickets": sla_breached,
        "active_agents": 0,
    }
