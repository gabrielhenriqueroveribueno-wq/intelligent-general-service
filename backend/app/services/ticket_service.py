import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import SLAConfig
from app.models.ticket import Ticket, TicketComment
from app.utils.exceptions import NotFoundError


def _generate_protocol(tenant_id: uuid.UUID) -> str:
    from datetime import datetime
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short = str(tenant_id).split("-")[0][:4].upper()
    return f"{short}-{ts}"


async def get_sla_deadline(
    db: AsyncSession, tenant_id: uuid.UUID, priority: str
) -> Optional[datetime]:
    result = await db.execute(
        select(SLAConfig).where(
            SLAConfig.tenant_id == tenant_id,
            SLAConfig.priority == priority,
            SLAConfig.is_active == True,
        )
    )
    sla = result.scalar_one_or_none()
    if sla:
        return datetime.now(timezone.utc) + timedelta(minutes=sla.resolution_time_minutes)
    return None


async def create_ticket(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    subject: str,
    priority: str = "medium",
    category: Optional[str] = None,
    description: Optional[str] = None,
    contact_id: Optional[uuid.UUID] = None,
    conversation_id: Optional[uuid.UUID] = None,
) -> Ticket:
    sla_deadline = await get_sla_deadline(db, tenant_id, priority)

    ticket = Ticket(
        tenant_id=tenant_id,
        protocol_number=_generate_protocol(tenant_id),
        subject=subject,
        priority=priority,
        category=category,
        description=description,
        contact_id=contact_id,
        conversation_id=conversation_id,
        sla_deadline=sla_deadline,
        status="open",
    )
    db.add(ticket)
    await db.flush()
    return ticket


async def list_tickets(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[uuid.UUID] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Ticket], int]:
    query = select(Ticket).where(Ticket.tenant_id == tenant_id)

    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assigned_to:
        query = query.where(Ticket.assigned_to == assigned_to)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.offset((page - 1) * size).limit(size).order_by(Ticket.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_ticket(
    db: AsyncSession, tenant_id: uuid.UUID, ticket_id: uuid.UUID
) -> Ticket:
    result = await db.execute(
        select(Ticket).where(Ticket.tenant_id == tenant_id, Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket")
    return ticket


async def add_comment(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    author_id: uuid.UUID,
    content: str,
    is_internal: bool = False,
) -> TicketComment:
    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=author_id,
        content=content,
        is_internal=is_internal,
    )
    db.add(comment)
    await db.flush()
    return comment
