import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.services.report_service import (
    get_conversation_report,
    get_ticket_report,
    rows_to_csv,
)
import io

router = APIRouter()


@router.get("/conversations")
async def export_conversations_csv(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
):
    rows = await get_conversation_report(db, tenant_id, start_date, end_date)
    csv_bytes = rows_to_csv(rows)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=conversations.csv"},
    )


@router.get("/tickets")
async def export_tickets_csv(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
):
    rows = await get_ticket_report(db, tenant_id, start_date, end_date)
    csv_bytes = rows_to_csv(rows)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tickets.csv"},
    )
