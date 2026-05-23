# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Tarefas de controle de trial dos tenants SaaS.

- Verifica trial_ends_at em tenant.settings
- Expira tenants com trial vencido
- Envia avisos 7d, 3d e 1d antes do vencimento
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.user import User
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_trial_ends_at(tenant: Tenant) -> datetime | None:
    """Lê trial_ends_at do JSONB settings. Retorna None se ausente."""
    if not tenant.settings:
        return None
    raw = tenant.settings.get("trial_ends_at")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


async def _run_trial_check() -> dict:
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.services.email_service import send_email_async

    now = datetime.now(timezone.utc)
    expired = []
    warned = []

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Tenant).where(Tenant.is_active.is_(True), Tenant.plan == "trial")
        )
        tenants = result.scalars().all()

        for tenant in tenants:
            trial_ends = _get_trial_ends_at(tenant)
            if not trial_ends:
                continue

            days_left = (trial_ends - now).days

            if trial_ends <= now:
                # Expirar o trial
                tenant.plan = "trial_expired"
                tenant.is_active = False
                expired.append(str(tenant.id))
                logger.info("Trial expirado: tenant=%s (%s)", tenant.id, tenant.name)

                # Notifica admins do tenant
                admin_result = await db.execute(
                    select(User).where(
                        User.tenant_id == tenant.id,
                        User.role.in_(["admin", "super_admin"]),
                        User.is_active.is_(True),
                    )
                )
                for admin in admin_result.scalars().all():
                    if admin.email:
                        await send_email_async(
                            to=admin.email,
                            subject="Seu período de trial IGS expirou",
                            body=(
                                f"<p>Olá, <strong>{admin.full_name or admin.email}</strong>!</p>"
                                f"<p>O período de trial da instituição <strong>{tenant.name}</strong> "
                                f"expirou em {trial_ends.strftime('%d/%m/%Y')}.</p>"
                                "<p>Para continuar usando o IGS, escolha um plano em "
                                "<a href='https://igs-anchieta.duckdns.org/pricing'>nosso site</a> "
                                "ou entre em contato com nossa equipe comercial.</p>"
                                "<p>Atenciosamente,<br>Equipe IGS</p>"
                            ),
                        )

            elif days_left in (7, 3, 1):
                # Aviso antecipado
                warned.append(str(tenant.id))
                days_label = f"{days_left} dia{'s' if days_left > 1 else ''}"
                logger.info(
                    "Aviso de trial: tenant=%s, dias restantes=%d", tenant.id, days_left
                )

                admin_result = await db.execute(
                    select(User).where(
                        User.tenant_id == tenant.id,
                        User.role.in_(["admin", "super_admin"]),
                        User.is_active.is_(True),
                    )
                )
                for admin in admin_result.scalars().all():
                    if admin.email:
                        await send_email_async(
                            to=admin.email,
                            subject=f"Seu trial IGS expira em {days_label}",
                            body=(
                                f"<p>Olá, <strong>{admin.full_name or admin.email}</strong>!</p>"
                                f"<p>O período de trial da instituição <strong>{tenant.name}</strong> "
                                f"expira em <strong>{days_label}</strong> "
                                f"({trial_ends.strftime('%d/%m/%Y')}).</p>"
                                "<p>Para não perder o acesso, escolha um plano em "
                                "<a href='https://igs-anchieta.duckdns.org/pricing'>nosso site</a>.</p>"
                                "<p>Atenciosamente,<br>Equipe IGS</p>"
                            ),
                        )

        await db.commit()

    return {"expired": expired, "warned": warned}


@celery_app.task(name="app.tasks.trial_tasks.check_trial_expiry_task", bind=True, max_retries=2)
def check_trial_expiry_task(self):
    """Verifica e expira trials vencidos; envia avisos em 7d/3d/1d."""
    try:
        result = asyncio.run(_run_trial_check())
        logger.info(
            "Trial check concluído: %d expirados, %d avisados",
            len(result["expired"]),
            len(result["warned"]),
        )
        return result
    except Exception as exc:
        logger.error("Erro no trial check: %s", exc)
        raise self.retry(exc=exc, countdown=300)
