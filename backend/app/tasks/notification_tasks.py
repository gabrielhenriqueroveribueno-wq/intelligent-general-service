import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def check_sla_task():
    """Verifica violações de SLA em todos os tenants."""
    asyncio.run(_check_sla_async())


async def _check_sla_async():
    from app.dependencies import AsyncSessionLocal
    from app.services.sla_service import check_sla_breaches

    async with AsyncSessionLocal() as db:
        breaches = await check_sla_breaches(db)
        if breaches:
            logger.warning("SLA violado em %d tickets", len(breaches))
            for b in breaches:
                logger.warning(
                    "SLA breach: tenant=%s ticket=%s priority=%s deadline=%s",
                    b["tenant_id"],
                    b["protocol"],
                    b["priority"],
                    b["deadline"],
                )
        await db.commit()
