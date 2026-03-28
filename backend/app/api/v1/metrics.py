"""
Endpoints de métricas comparativas IA vs Humano e ROI.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import metrics_service

router = APIRouter()


class MonitoredAccountCreate(BaseModel):
    account_name: str
    phone_number: str
    account_type: str = "mixed"
    notes: Optional[str] = None


@router.get("/comparison")
async def comparison_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Relatório comparativo IA vs Humano."""
    return await metrics_service.get_comparison_report(db, user.tenant_id, start_date, end_date)


@router.get("/roi")
async def roi_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cálculo de ROI da IA."""
    return await metrics_service.calculate_roi(db, user.tenant_id)


@router.get("/dashboard")
async def metrics_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dados consolidados para o dashboard de métricas."""
    return await metrics_service.get_dashboard_data(db, user.tenant_id)


@router.get("/monitored-accounts")
async def list_monitored_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista contas WhatsApp monitoradas."""
    accounts = await metrics_service.list_monitored_accounts(db, user.tenant_id)
    return [
        {
            "id": str(a.id),
            "account_name": a.account_name,
            "phone_number": a.phone_number,
            "account_type": a.account_type,
            "is_active": a.is_active,
            "monitoring_start_date": a.monitoring_start_date.isoformat()
            if a.monitoring_start_date
            else None,
            "notes": a.notes,
        }
        for a in accounts
    ]


@router.post("/monitored-accounts")
async def create_monitored_account(
    data: MonitoredAccountCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Adiciona conta WhatsApp para monitoramento."""
    account = await metrics_service.create_monitored_account(
        db=db,
        tenant_id=user.tenant_id,
        account_name=data.account_name,
        phone_number=data.phone_number,
        account_type=data.account_type,
        notes=data.notes,
    )
    await db.commit()
    return {"id": str(account.id), "message": "Conta adicionada com sucesso."}
