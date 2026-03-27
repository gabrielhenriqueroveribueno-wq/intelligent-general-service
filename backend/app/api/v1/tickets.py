import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.schemas.ticket import (
    TicketCommentCreate,
    TicketCommentResponse,
    TicketCreate,
    TicketDetailResponse,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services import ticket_service

router = APIRouter()


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    ticket = await ticket_service.create_ticket(
        db,
        tenant_id=tenant_id,
        subject=body.subject,
        priority=body.priority,
        category=body.category,
        description=body.description,
        contact_id=body.contact_id,
        conversation_id=body.conversation_id,
    )

    # Dispara webhook de saída
    try:
        from app.services.webhook_delivery_service import dispatch_event
        await dispatch_event(db, tenant_id, "ticket.created", {
            "ticket_id": str(ticket.id),
            "subject": ticket.subject,
            "priority": ticket.priority,
            "category": ticket.category,
        })
    except Exception:
        pass

    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    tickets, total = await ticket_service.list_tickets(db, tenant_id, status, priority, page=page, size=size)
    return TicketListResponse(
        items=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    from app.models.ticket import TicketComment

    ticket = await ticket_service.get_ticket(db, tenant_id, ticket_id)
    comments_result = await db.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at)
    )
    comments = comments_result.scalars().all()
    detail = TicketDetailResponse.model_validate(ticket)
    detail.comments = [TicketCommentResponse.model_validate(c) for c in comments]
    return detail


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    body: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    from datetime import datetime, timezone

    ticket = await ticket_service.get_ticket(db, tenant_id, ticket_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ticket, field, value)
    if body.status == "resolved":
        ticket.resolved_at = datetime.now(timezone.utc)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=201)
async def add_comment(
    ticket_id: uuid.UUID,
    body: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    comment = await ticket_service.add_comment(
        db, ticket_id, current_user.id, body.content, body.is_internal
    )
    return TicketCommentResponse.model_validate(comment)
