"""
Endpoints administrativos (super_admin apenas).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.models.audit import FailedTask
from app.utils.exceptions import NotFoundError

router = APIRouter()


@router.get("/failed-tasks")
async def list_failed_tasks(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
    resolved: Optional[bool] = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """Lista tarefas que falharam após todas as tentativas."""
    query = select(FailedTask).where(FailedTask.resolved == resolved)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(FailedTask.failed_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "items": [
            {
                "id": str(t.id),
                "task_id": t.task_id,
                "task_name": t.task_name,
                "args": t.args,
                "error_message": t.error_message,
                "retry_count": t.retry_count,
                "failed_at": t.failed_at.isoformat() if t.failed_at else None,
                "tenant_id": str(t.tenant_id) if t.tenant_id else None,
                "resolved": t.resolved,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in tasks
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/failed-tasks/{task_id}/retry", status_code=202)
async def retry_failed_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    """Reenfileira uma tarefa falhada para reprocessamento."""
    result = await db.execute(select(FailedTask).where(FailedTask.id == task_id))
    failed = result.scalar_one_or_none()
    if not failed:
        raise NotFoundError("Tarefa falhada")

    from app.tasks.dlq_tasks import retry_failed_task as _retry

    _retry.delay(str(task_id))

    return {"message": "Tarefa reenfileirada para reprocessamento", "task_id": str(task_id)}
