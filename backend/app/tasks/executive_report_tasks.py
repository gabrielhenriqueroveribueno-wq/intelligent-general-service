"""
Tasks Celery para enviar relatorios executivos por email.

- dispatch_scheduled_reports_task: roda de hora em hora, checa quais subscricoes
  precisam ser enviadas hoje e dispara envios
- send_subscription_report_task(subscription_id): envia relatorio de uma
  subscricao especifica (usado pela dispatch e pelo botao "enviar teste")

Dedupe: usamos last_sent_at pra evitar duplicatas se a task rodar mais de uma
vez no mesmo slot de horario.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Dispatcher (hourly)
# ══════════════════════════════════════════════════════════════════════════════


@celery_app.task(name="app.tasks.executive_report_tasks.dispatch_scheduled_reports_task")
def dispatch_scheduled_reports_task():
    """Roda a cada hora; despacha envio de subscricoes cujo slot bateu agora."""
    asyncio.run(_dispatch_async())


async def _dispatch_async() -> None:
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.report_subscription import ReportSubscription

    now = datetime.now(timezone.utc)
    current_hour = now.hour
    today = now.date()

    async with AsyncSessionLocal() as db:
        subs = await db.execute(
            select(ReportSubscription).where(
                ReportSubscription.is_active,
                ReportSubscription.send_hour_utc == current_hour,
            )
        )
        for sub in subs.scalars().all():
            if not _should_send_today(sub, today):
                continue
            if sub.last_sent_at and sub.last_sent_at.date() == today:
                continue  # dedupe

            # Enfileira o envio — task separada pra ter retry independente
            send_subscription_report_task.delay(str(sub.id))
            logger.info(
                "Agendado envio de relatorio: subscription=%s tenant=%s period=%s",
                sub.id, sub.tenant_id, sub.period,
            )


def _should_send_today(sub, today) -> bool:
    if sub.period == "daily":
        return True
    if sub.period == "weekly":
        # segunda-feira (weekday==0)
        return today.weekday() == 0
    if sub.period == "monthly":
        return today.day == 1
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Single subscription sender
# ══════════════════════════════════════════════════════════════════════════════


@celery_app.task(
    name="app.tasks.executive_report_tasks.send_subscription_report_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_subscription_report_task(self, subscription_id: str):
    """Envia relatorio de UMA subscricao especifica."""
    try:
        asyncio.run(_send_single_async(subscription_id))
    except Exception as exc:
        logger.exception("Erro enviando relatorio subscription=%s", subscription_id)
        raise self.retry(exc=exc)


async def _send_single_async(subscription_id: str) -> None:
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.report_subscription import ReportSubscription
    from app.models.tenant import Tenant
    from app.services import executive_report_service
    from app.services.email_service import send_email

    async with AsyncSessionLocal() as db:
        sub = (await db.execute(
            select(ReportSubscription).where(ReportSubscription.id == uuid.UUID(subscription_id))
        )).scalar_one_or_none()
        if not sub:
            logger.warning("Subscription %s nao encontrada", subscription_id)
            return
        if not sub.recipients:
            logger.warning("Subscription %s sem destinatarios", subscription_id)
            return

        tenant = (await db.execute(
            select(Tenant).where(Tenant.id == sub.tenant_id)
        )).scalar_one_or_none()
        if not tenant:
            logger.warning("Tenant %s nao encontrado", sub.tenant_id)
            return

        data = await executive_report_service.build_report(
            db, sub.tenant_id, tenant.name, period=sub.period  # type: ignore[arg-type]
        )
        html = executive_report_service.render_report_html(data)
        subject = executive_report_service.render_subject(data)

        sent_count = 0
        for email in sub.recipients:
            email = email.strip()
            if not email:
                continue
            try:
                ok = send_email(to=email, subject=subject, body=html)
                if ok:
                    sent_count += 1
            except Exception as exc:
                logger.error("Falha enviando pro email %s: %s", email, exc)

        sub.last_sent_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(
            "Relatorio %s enviado: subscription=%s destinatarios=%d/%d",
            sub.period, sub.id, sent_count, len(sub.recipients),
        )


# ══════════════════════════════════════════════════════════════════════════════
# Ad-hoc send (called from admin endpoint)
# ══════════════════════════════════════════════════════════════════════════════


async def send_ad_hoc_report(
    db,
    tenant_id: uuid.UUID,
    tenant_name: str,
    period: str,
    recipients: list[str],
) -> dict:
    """
    Envia relatorio imediato pra lista de emails (sem depender de subscription).
    Usado pelo endpoint 'Enviar teste agora'.
    """
    from app.services import executive_report_service
    from app.services.email_service import send_email

    data = await executive_report_service.build_report(
        db, tenant_id, tenant_name, period=period  # type: ignore[arg-type]
    )
    html = executive_report_service.render_report_html(data)
    subject = executive_report_service.render_subject(data)

    sent = 0
    failed: list[str] = []
    for email in recipients:
        email = email.strip()
        if not email:
            continue
        try:
            ok = send_email(to=email, subject=subject, body=html)
            if ok:
                sent += 1
            else:
                failed.append(email)
        except Exception as exc:
            logger.error("Falha enviando para %s: %s", email, exc)
            failed.append(email)

    return {
        "sent": sent,
        "failed": failed,
        "subject": subject,
        "period": period,
    }
