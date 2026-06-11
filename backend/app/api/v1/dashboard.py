import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.schemas.dashboard import DashboardInsights, DashboardOverview
from app.services.report_service import get_dashboard_insights, get_dashboard_overview

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    return await get_dashboard_overview(db, tenant_id)


@router.get("/insights", response_model=DashboardInsights)
async def dashboard_insights(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    """Volume diario 7d, top intents, sentimento, CSAT e custo de IA do mes."""
    return await get_dashboard_insights(db, tenant_id)
