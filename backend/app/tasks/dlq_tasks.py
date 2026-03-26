"""
Dead Letter Queue — tarefas auxiliares para persistir e reprocessar falhas.
"""
import asyncio
import logging
from typing import Optional

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def save_failed_task_async(
    task_id: str,
    task_name: str,
    args: dict,
    error_message: str,
    traceback: Optional[str] = None,
    retry_count: int = 0,
    tenant_id: Optional[str] = None,
):
    """Persiste registro de tarefa falhada no banco."""
    from datetime import datetime, timezone
    from app.dependencies import AsyncSessionLocal
    from app.models.audit import FailedTask

    async with AsyncSessionLocal() as db:
        failed = FailedTask(
            task_id=task_id,
            task_name=task_name,
            args=args,
            error_message=error_message,
            traceback=traceback,
            retry_count=retry_count,
            failed_at=datetime.now(timezone.utc),
        )
        db.add(failed)
        await db.commit()
        logger.error(
            "Tarefa persistida no DLQ: task_id=%s task_name=%s error=%s",
            task_id, task_name, error_message,
        )


@celery_app.task(bind=True)
def retry_failed_task(self, failed_task_id: str):
    """Recoloca uma tarefa falhada na fila para reprocessamento."""
    asyncio.run(_retry_async(failed_task_id))


async def _retry_async(failed_task_id: str):
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import select, update
    from app.dependencies import AsyncSessionLocal
    from app.models.audit import FailedTask

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FailedTask).where(FailedTask.id == uuid.UUID(failed_task_id))
        )
        failed = result.scalar_one_or_none()
        if not failed or failed.resolved:
            logger.warning("FailedTask não encontrada ou já resolvida: %s", failed_task_id)
            return

        # Re-enfileira a tarefa original
        from app.tasks.message_tasks import process_incoming_message
        message_id = failed.args.get("message_id") if failed.args else None
        if message_id:
            process_incoming_message.delay(message_id)

        await db.execute(
            update(FailedTask)
            .where(FailedTask.id == uuid.UUID(failed_task_id))
            .values(resolved=True, resolved_at=datetime.now(timezone.utc))
        )
        await db.commit()
        logger.info("Tarefa %s reenfileirada com sucesso", failed_task_id)
