import asyncio
import logging
import uuid

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
# Retry com backoff exponencial: 1min, 2min, 4min, 8min, 16min
COUNTDOWN = [60, 120, 240, 480, 960]


@celery_app.task(
    bind=True,
    name="app.tasks.webhook_tasks.deliver_webhook_task",
    max_retries=MAX_RETRIES,
    acks_late=True,
)
def deliver_webhook_task(self, delivery_id: str) -> None:
    """Entrega um WebhookDelivery ao endpoint externo com retry exponencial."""
    asyncio.run(_deliver(self, uuid.UUID(delivery_id)))


async def _deliver(task, delivery_id: uuid.UUID) -> None:
    from app.dependencies import AsyncSessionLocal
    from app.services.webhook_delivery_service import send_delivery

    async with AsyncSessionLocal() as db:
        success = await send_delivery(db, delivery_id)

    if not success:
        attempt = task.request.retries + 1
        if attempt <= MAX_RETRIES:
            countdown = COUNTDOWN[min(attempt - 1, len(COUNTDOWN) - 1)]
            logger.warning(
                "Webhook delivery falhou (tentativa %d/%d), retry em %ds: %s",
                attempt, MAX_RETRIES, countdown, delivery_id,
            )
            raise task.retry(countdown=countdown)
        else:
            logger.error("Webhook delivery esgotou tentativas: %s", delivery_id)
