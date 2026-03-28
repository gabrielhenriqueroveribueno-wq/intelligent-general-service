"""
Serviço de métricas comparativas IA vs Humano.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Float, and_, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metrics import ResponseTimeMetric, WhatsAppMonitoredAccount
from app.models.satisfaction import SatisfactionSurvey

logger = logging.getLogger(__name__)


async def record_response_time(
    db: AsyncSession,
    tenant_id: UUID,
    conversation_id: UUID,
    message_id: UUID,
    responder_type: str,
    response_time: float,
    message_count: int | None = None,
    was_resolved: bool = False,
    resolution_time: float | None = None,
) -> ResponseTimeMetric:
    """Registra uma métrica de tempo de resposta."""
    metric = ResponseTimeMetric(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        message_id=message_id,
        responder_type=responder_type,
        response_time_seconds=response_time,
        message_count_in_conversation=message_count,
        was_resolved=was_resolved,
        resolution_time_total_seconds=resolution_time,
    )
    db.add(metric)
    await db.flush()
    return metric


async def get_comparison_report(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Retorna relatório comparativo IA vs Humano."""
    filters = [ResponseTimeMetric.tenant_id == tenant_id]
    if start_date:
        filters.append(ResponseTimeMetric.created_at >= start_date)
    if end_date:
        filters.append(ResponseTimeMetric.created_at <= end_date)

    combined = and_(*filters)

    # Tempo médio por tipo
    avg_result = await db.execute(
        select(
            ResponseTimeMetric.responder_type,
            func.avg(ResponseTimeMetric.response_time_seconds).label("avg_time"),
            func.count().label("total"),
            func.avg(
                case(
                    (ResponseTimeMetric.was_resolved.is_(True), 1.0),
                    else_=0.0,
                )
            ).label("resolution_rate"),
        )
        .where(combined)
        .group_by(ResponseTimeMetric.responder_type)
    )
    rows = avg_result.all()

    by_type: dict[str, dict[str, Any]] = {}
    for row in rows:
        by_type[row[0]] = {
            "avg_response_time_seconds": round(float(row[1]), 2) if row[1] else 0,
            "total_interactions": row[2],
            "resolution_rate": round(float(row[3]) * 100, 1) if row[3] else 0,
        }

    # Satisfação média por tipo
    sat_filters = [SatisfactionSurvey.tenant_id == tenant_id]
    if start_date:
        sat_filters.append(SatisfactionSurvey.created_at >= start_date)
    if end_date:
        sat_filters.append(SatisfactionSurvey.created_at <= end_date)

    sat_result = await db.execute(
        select(
            SatisfactionSurvey.responder_type,
            func.avg(cast(SatisfactionSurvey.score, Float)).label("avg_score"),
        )
        .where(
            and_(*sat_filters),
            SatisfactionSurvey.score.is_not(None),
        )
        .group_by(SatisfactionSurvey.responder_type)
    )
    for row in sat_result.all():
        if row[0] in by_type:
            by_type[row[0]]["avg_satisfaction"] = round(float(row[1]), 2) if row[1] else None

    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
        "by_responder_type": by_type,
    }


async def calculate_roi(
    db: AsyncSession,
    tenant_id: UUID,
    human_cost_per_month: float = 3000.0,
    human_capacity_per_month: int = 600,
    ai_cost_per_token: float = 0.000015,
    avg_tokens_per_interaction: int = 800,
) -> dict[str, Any]:
    """
    Calcula ROI da IA vs atendentes humanos.
    """
    # Total de interações por tipo (último mês)
    result = await db.execute(
        select(
            ResponseTimeMetric.responder_type,
            func.count().label("total"),
            func.avg(ResponseTimeMetric.response_time_seconds).label("avg_time"),
        )
        .where(ResponseTimeMetric.tenant_id == tenant_id)
        .group_by(ResponseTimeMetric.responder_type)
    )
    rows = result.all()

    bot_count = 0
    bot_avg_time = 0.0
    human_count = 0
    human_avg_time = 0.0

    for row in rows:
        if row[0] == "bot":
            bot_count = row[1]
            bot_avg_time = float(row[2]) if row[2] else 0
        elif row[0] in ("human", "agent"):
            human_count += row[1]
            human_avg_time = float(row[2]) if row[2] else 0

    # Custos estimados
    ai_monthly_cost = bot_count * avg_tokens_per_interaction * ai_cost_per_token
    humans_needed = max(1, human_count / human_capacity_per_month) if human_count else 1
    human_monthly_cost = humans_needed * human_cost_per_month

    # Se a IA não existisse, todos os atendimentos seriam humanos
    total = bot_count + human_count
    hypothetical_humans = max(1, total / human_capacity_per_month) if total else 1
    hypothetical_cost = hypothetical_humans * human_cost_per_month

    savings = hypothetical_cost - (ai_monthly_cost + human_monthly_cost)
    savings_pct = (savings / hypothetical_cost * 100) if hypothetical_cost > 0 else 0

    time_saved = (human_avg_time - bot_avg_time) if human_avg_time and bot_avg_time else 0

    return {
        "bot_interactions": bot_count,
        "human_interactions": human_count,
        "ai_monthly_cost": round(ai_monthly_cost, 2),
        "human_monthly_cost": round(human_monthly_cost, 2),
        "hypothetical_full_human_cost": round(hypothetical_cost, 2),
        "monthly_savings": round(savings, 2),
        "savings_percentage": round(savings_pct, 1),
        "avg_time_saved_per_interaction_seconds": round(time_saved, 2),
    }


async def get_dashboard_data(
    db: AsyncSession,
    tenant_id: UUID,
) -> dict[str, Any]:
    """Dados consolidados para o dashboard de métricas."""
    comparison = await get_comparison_report(db, tenant_id)
    roi = await calculate_roi(db, tenant_id)

    # Total de atendimentos
    total_result = await db.execute(
        select(func.count()).where(ResponseTimeMetric.tenant_id == tenant_id)
    )
    total = total_result.scalar() or 0

    return {
        "total_interactions": total,
        "comparison": comparison,
        "roi": roi,
    }


async def list_monitored_accounts(
    db: AsyncSession,
    tenant_id: UUID,
) -> list[WhatsAppMonitoredAccount]:
    """Lista contas WhatsApp monitoradas."""
    result = await db.execute(
        select(WhatsAppMonitoredAccount).where(WhatsAppMonitoredAccount.tenant_id == tenant_id)
    )
    return list(result.scalars().all())


async def create_monitored_account(
    db: AsyncSession,
    tenant_id: UUID,
    account_name: str,
    phone_number: str,
    account_type: str = "mixed",
    notes: str | None = None,
) -> WhatsAppMonitoredAccount:
    """Adiciona conta WhatsApp para monitoramento."""
    account = WhatsAppMonitoredAccount(
        tenant_id=tenant_id,
        account_name=account_name,
        phone_number=phone_number,
        account_type=account_type,
        notes=notes,
    )
    db.add(account)
    await db.flush()
    return account
