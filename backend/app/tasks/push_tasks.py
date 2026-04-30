from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def send_ticket_push_task(self, ticket_id: str, tenant_id: str) -> None:
    """Send Web Push to all admin users of the tenant when a ticket is created."""
    try:
        asyncio.run(_send_ticket_push(ticket_id, tenant_id))
    except Exception as exc:
        logger.warning("push_ticket retry %s: %s", ticket_id, exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, max_retries=2)
def send_sla_breach_push_task(self, ticket_id: str, tenant_id: str) -> None:
    """Send Web Push when a ticket breaches SLA."""
    try:
        asyncio.run(_send_sla_breach_push(ticket_id, tenant_id))
    except Exception as exc:
        logger.warning("push_sla retry %s: %s", ticket_id, exc)
        raise self.retry(exc=exc, countdown=30)


async def _get_tenant_subscriptions(db, tenant_id: str):
    from sqlalchemy import select

    from app.models.push_subscription import PushSubscription
    from app.models.user import User

    result = await db.execute(
        select(PushSubscription).join(User, User.id == PushSubscription.user_id).where(
            User.tenant_id == tenant_id
        )
    )
    return result.scalars().all()


@celery_app.task(bind=True, max_retries=2)
def send_handoff_push_task(self, conversation_id: str, tenant_id: str, contact_name: str) -> None:
    """Send Web Push to all agents when bot requests human handoff."""
    try:
        asyncio.run(_send_handoff_push(conversation_id, tenant_id, contact_name))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=15)


async def _send_handoff_push(conversation_id: str, tenant_id: str, contact_name: str) -> None:
    from app.dependencies import WorkerSessionLocal
    from app.services.push_notification_service import send_push_to_many

    async with WorkerSessionLocal() as db:
        subs = await _get_tenant_subscriptions(db, tenant_id)
        if not subs:
            return
        _, expired = send_push_to_many(
            subs,
            title="Atendimento Humano Solicitado",
            body=f"{contact_name} precisa de um agente",
            url="/app/conversations",
        )
        await _purge_expired(db, expired)


async def _purge_expired(db, expired_endpoints: list[str]) -> None:
    if not expired_endpoints:
        return
    from sqlalchemy import delete

    from app.models.push_subscription import PushSubscription

    for ep in expired_endpoints:
        await db.execute(
            delete(PushSubscription).where(PushSubscription.endpoint == ep)
        )
    await db.commit()


async def _send_ticket_push(ticket_id: str, tenant_id: str) -> None:
    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal
    from app.models.ticket import Ticket
    from app.services.push_notification_service import send_push_to_many

    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            return

        subs = await _get_tenant_subscriptions(db, tenant_id)
        if not subs:
            return

        _, expired = send_push_to_many(
            subs,
            title="Novo Ticket Aberto",
            body=f"#{ticket.id[:8].upper()} — {ticket.title}",
            url="/app/tickets",
        )
        await _purge_expired(db, expired)


async def _send_sla_breach_push(ticket_id: str, tenant_id: str) -> None:
    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal
    from app.models.ticket import Ticket
    from app.services.push_notification_service import send_push_to_many

    async with WorkerSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            return

        subs = await _get_tenant_subscriptions(db, tenant_id)
        if not subs:
            return

        _, expired = send_push_to_many(
            subs,
            title="⚠️ SLA Violado",
            body=f"Ticket #{ticket.id[:8].upper()} passou do prazo: {ticket.title}",
            url="/app/tickets",
        )
        await _purge_expired(db, expired)
