import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.metrics_middleware import sla_breaches_total
from app.models.ticket import Ticket


async def check_sla_breaches(db: AsyncSession) -> list[dict]:
    """
    Verifica tickets que violaram o SLA.
    Chamado periodicamente pelo Celery Beat.
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Ticket).where(
            Ticket.status.in_(["open", "in_progress"]),
            Ticket.sla_deadline < now,
        )
    )
    breached = result.scalars().all()

    breaches = []
    for ticket in breached:
        breaches.append(
            {
                "ticket_id": str(ticket.id),
                "protocol": ticket.protocol_number,
                "priority": ticket.priority,
                "tenant_id": str(ticket.tenant_id),
                "deadline": ticket.sla_deadline.isoformat(),
            }
        )
        # Emite métrica Prometheus
        sla_breaches_total.labels(
            tenant_id=str(ticket.tenant_id),
            priority=ticket.priority,
        ).inc()

    return breaches
