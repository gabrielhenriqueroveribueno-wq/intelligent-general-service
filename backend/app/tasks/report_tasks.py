import asyncio
import logging
import uuid
from datetime import datetime

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def generate_report_task(tenant_id: str, report_type: str, start_date: str, end_date: str) -> str:
    """Gera relatório em background e retorna CSV como string."""
    return asyncio.run(
        _generate_report(
            uuid.UUID(tenant_id),
            report_type,
            datetime.fromisoformat(start_date),
            datetime.fromisoformat(end_date),
        )
    )


async def _generate_report(
    tenant_id: uuid.UUID,
    report_type: str,
    start_date: datetime,
    end_date: datetime,
) -> str:
    from app.dependencies import AsyncSessionLocal
    from app.services.report_service import get_conversation_report, get_ticket_report, rows_to_csv

    async with AsyncSessionLocal() as db:
        if report_type == "conversations":
            rows = await get_conversation_report(db, tenant_id, start_date, end_date)
        elif report_type == "tickets":
            rows = await get_ticket_report(db, tenant_id, start_date, end_date)
        else:
            rows = []

        csv_bytes = rows_to_csv(rows)
        return csv_bytes.decode("utf-8-sig")
