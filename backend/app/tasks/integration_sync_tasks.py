"""
Tasks Celery para sincronizar dados de sistemas academicos externos.

- dispatch_integration_syncs_task: roda a cada hora; checa quais integracoes
  precisam sincronizar com base no sync_cron de cada uma
- run_integration_sync_task(integration_id): executa sync de UMA integracao

Atualiza last_sync_at, last_sync_duration_ms, last_sync_records_synced,
last_sync_error e status para 'active' ou 'error' apos cada execucao.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Dispatcher (hourly)
# ══════════════════════════════════════════════════════════════════════════════


@celery_app.task(name="app.tasks.integration_sync_tasks.dispatch_integration_syncs_task")
def dispatch_integration_syncs_task():
    """Dispara sincronizacoes que precisam rodar agora."""
    asyncio.run(_dispatch_async())


async def _dispatch_async() -> None:
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.academic_integration import AcademicIntegration

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AcademicIntegration).where(AcademicIntegration.status == "active")
        )
        for integ in result.scalars().all():
            if not _is_due(integ):
                continue
            run_integration_sync_task.delay(str(integ.id))
            logger.info(
                "Sync agendada: integration=%s tenant=%s provider=%s",
                integ.id,
                integ.tenant_id,
                integ.provider_type,
            )


def _is_due(integ) -> bool:
    """
    Checa se integ precisa rodar agora baseado em sync_cron.

    Implementacao simplificada: parse minimal do cron pra suportar
    os casos comuns (a cada N horas, diariamente). Para regras complexas,
    o usuario deve editar manualmente o cron.
    """
    if not integ.last_sync_at:
        return True

    now = datetime.now(timezone.utc)
    cron = (integ.sync_cron or "0 */6 * * *").strip()

    # Ex: "0 */6 * * *" — a cada 6 horas
    parts = cron.split()
    if len(parts) != 5:
        return False

    minute, hour, *_ = parts

    # Suporte ao padrao "*/N" em hour
    if hour.startswith("*/"):
        try:
            interval_h = int(hour[2:])
        except ValueError:
            interval_h = 6
        return now - integ.last_sync_at >= timedelta(hours=interval_h)

    # Hora fixa diaria
    try:
        target_hour = int(hour)
        target_min = int(minute)
        if now.hour == target_hour and now.minute >= target_min:
            # Nao rodou hoje?
            return integ.last_sync_at.date() < now.date()
    except ValueError:
        pass

    return False


# ══════════════════════════════════════════════════════════════════════════════
# Single integration sync
# ══════════════════════════════════════════════════════════════════════════════


@celery_app.task(
    name="app.tasks.integration_sync_tasks.run_integration_sync_task",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def run_integration_sync_task(self, integration_id: str):
    """Roda sync de UMA integracao. Atualiza status no banco."""
    try:
        asyncio.run(_run_sync_async(integration_id))
    except Exception as exc:
        logger.exception("Erro fatal sync integration=%s", integration_id)
        raise self.retry(exc=exc)


async def _run_sync_async(integration_id: str) -> None:
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.academic_integration import AcademicIntegration
    from app.models.sync_log import SyncLog
    from app.services.integrations.registry import decrypt_credentials, get_integrator

    async with AsyncSessionLocal() as db:
        integ = (
            await db.execute(
                select(AcademicIntegration).where(
                    AcademicIntegration.id == uuid.UUID(integration_id)
                )
            )
        ).scalar_one_or_none()

        if not integ:
            logger.warning("Integration %s nao encontrada", integration_id)
            return

        creds = decrypt_credentials(integ.credentials_encrypted)
        started_at = datetime.now(timezone.utc)

        log = SyncLog(
            id=uuid.uuid4(),
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
            started_at=started_at,
            status="running",
        )
        db.add(log)
        await db.flush()

        try:
            integrator = get_integrator(integ.provider_type, integ.config, creds)
        except ValueError as exc:
            integ.status = "error"
            integ.last_sync_error = str(exc)
            log.status = "error"
            log.finished_at = datetime.now(timezone.utc)
            log.error_summary = str(exc)[:500]
            await db.commit()
            return

        start = time.perf_counter()
        try:
            result = await integrator.sync_all(db, integ.tenant_id)
            await db.commit()
        except Exception as exc:
            await db.rollback()
            now = datetime.now(timezone.utc)
            integ.status = "error"
            integ.last_sync_error = str(exc)[:500]
            integ.last_sync_at = now
            log.status = "error"
            log.finished_at = now
            log.duration_ms = int((time.perf_counter() - start) * 1000)
            log.error_summary = str(exc)[:500]
            await db.commit()
            logger.exception("Sync falhou: integration=%s", integration_id)
            return

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        now = datetime.now(timezone.utc)

        integ.last_sync_at = now
        integ.last_sync_duration_ms = elapsed_ms
        integ.last_sync_records_synced = result.records_synced
        if result.success and not result.errors:
            integ.status = "active"
            integ.last_sync_error = None
            log.status = "success"
        elif result.errors:
            integ.status = "error"
            integ.last_sync_error = "; ".join(result.errors[:3])[:500]
            log.status = "partial" if result.records_synced > 0 else "error"

        log.finished_at = now
        log.duration_ms = elapsed_ms
        log.records_synced = result.records_synced
        log.students_created = result.students_created
        log.students_updated = result.students_updated
        log.employees_created = result.employees_created
        log.employees_updated = result.employees_updated
        log.errors = result.errors[:20] if result.errors else None
        log.warnings = result.warnings[:20] if result.warnings else None
        log.error_summary = "; ".join(result.errors[:3])[:500] if result.errors else None
        await db.commit()

        logger.info(
            "Sync completa: integration=%s registros=%d duracao=%dms erros=%d",
            integration_id,
            result.records_synced,
            elapsed_ms,
            len(result.errors),
        )
