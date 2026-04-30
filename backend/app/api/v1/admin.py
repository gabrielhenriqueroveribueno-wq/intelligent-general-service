"""
Endpoints administrativos (super_admin apenas).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.models.audit import AuditLog, FailedTask
from app.models.tenant import Tenant
from app.models.user import User
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


# ── Audit Logs ───────────────────────────────────────────────────────────────


@router.get("/audit-logs")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles("super_admin", "admin")),
    action: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=30, ge=1, le=100),
):
    """Lista o log de auditoria do tenant."""
    from sqlalchemy import and_

    filters = [AuditLog.tenant_id == current_user.tenant_id]
    if action:
        filters.append(AuditLog.action.ilike(f"%{action}%"))

    query = select(AuditLog).where(and_(*filters))
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(lg.id),
                "user_id": str(lg.user_id) if lg.user_id else None,
                "action": lg.action,
                "entity_type": lg.entity_type,
                "entity_id": str(lg.entity_id) if lg.entity_id else None,
                "details": lg.details,
                "ip_address": lg.ip_address,
                "created_at": lg.created_at.isoformat() if lg.created_at else None,
            }
            for lg in logs
        ],
        "total": total,
        "page": page,
        "size": size,
    }


# ── LGPD: Direito ao Esquecimento ────────────────────────────────────────────


@router.post("/lgpd/anonymize/student/{student_id}")
async def anonymize_student_endpoint(
    student_id: uuid.UUID,
    reason: str = Body(default="Solicitação do titular (Art. 18, LGPD)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    """Anonimiza todos os dados PII de um aluno (LGPD Art. 18 — Direito ao Esquecimento)."""
    from app.services.anonymization_service import anonymize_student

    result = await anonymize_student(
        db=db,
        tenant_id=current_user.tenant_id,
        student_id=student_id,
        reason=reason,
        requested_by=current_user.id,
    )
    return result


# ── Super Admin: MRR / Tenant Overview ───────────────────────────────────────

PLAN_PRICES: dict[str, float] = {
    "starter": 297.0,
    "pro": 497.0,
    "trial": 0.0,
    "enterprise": 0.0,
    "basic": 0.0,
}


@router.get("/super/overview")
async def super_overview(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    """Visão geral SaaS: MRR, tenants ativos, churn, planos."""
    now = datetime.now(timezone.utc)
    last_30 = now - timedelta(days=30)

    total_tenants = (await db.execute(select(func.count()).select_from(Tenant))).scalar() or 0
    active_tenants = (
        await db.execute(select(func.count()).select_from(Tenant).where(Tenant.is_active.is_(True)))
    ).scalar() or 0
    inactive_tenants = total_tenants - active_tenants

    new_last_30 = (
        await db.execute(
            select(func.count()).select_from(Tenant).where(Tenant.created_at >= last_30)
        )
    ).scalar() or 0

    # MRR: soma dos preços por plano dos tenants ativos
    tenants_result = await db.execute(
        select(Tenant.plan, func.count(Tenant.id))
        .where(Tenant.is_active.is_(True))
        .group_by(Tenant.plan)
    )
    plan_counts: dict[str, int] = {row[0]: row[1] for row in tenants_result.all()}

    mrr = sum(PLAN_PRICES.get(plan, 0.0) * count for plan, count in plan_counts.items())

    # Churn rate (últimos 30d): tenants que ficaram inativos / total do início do período
    churned_30 = (
        await db.execute(
            select(func.count())
            .select_from(Tenant)
            .where(Tenant.is_active.is_(False), Tenant.updated_at >= last_30)
        )
    ).scalar() or 0

    churn_rate = round(churned_30 / total_tenants * 100, 1) if total_tenants else 0.0

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "inactive_tenants": inactive_tenants,
        "new_last_30_days": new_last_30,
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "churn_rate_30d": churn_rate,
        "churned_last_30_days": churned_30,
        "plan_breakdown": plan_counts,
    }


@router.get("/super/tenants")
async def super_tenants(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
    search: Optional[str] = Query(default=None),
    plan: Optional[str] = Query(default=None),
    active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
):
    """Lista paginada de todos os tenants com métricas de billing."""
    from sqlalchemy import and_, or_

    filters = []
    if search:
        filters.append(or_(Tenant.name.ilike(f"%{search}%"), Tenant.slug.ilike(f"%{search}%")))
    if plan:
        filters.append(Tenant.plan == plan)
    if active is not None:
        filters.append(Tenant.is_active.is_(active))

    base_q = select(Tenant)
    if filters:
        base_q = base_q.where(and_(*filters))

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    base_q = base_q.order_by(Tenant.created_at.desc()).offset((page - 1) * size).limit(size)
    tenants = (await db.execute(base_q)).scalars().all()

    # Count admin users per tenant in one query
    tenant_ids = [t.id for t in tenants]
    user_counts_result = await db.execute(
        select(User.tenant_id, func.count(User.id))
        .where(User.tenant_id.in_(tenant_ids))
        .group_by(User.tenant_id)
    )
    user_counts: dict[uuid.UUID, int] = {row[0]: row[1] for row in user_counts_result.all()}

    items = [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "plan": t.plan,
            "is_active": t.is_active,
            "monthly_revenue": PLAN_PRICES.get(t.plan, 0.0),
            "user_count": user_counts.get(t.id, 0),
            "whatsapp_configured": bool(t.whatsapp_phone_number_id),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tenants
    ]

    return {"items": items, "total": total, "page": page, "size": size}


@router.patch("/super/tenants/{tenant_id}")
async def super_update_tenant(
    tenant_id: uuid.UUID,
    is_active: Optional[bool] = Body(default=None),
    plan: Optional[str] = Body(default=None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    """Ativa/suspende tenant ou muda plano."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise NotFoundError("Tenant")

    if is_active is not None:
        tenant.is_active = is_active
    if plan is not None:
        tenant.plan = plan

    await db.commit()
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "plan": tenant.plan,
        "is_active": tenant.is_active,
    }


# ── LGPD: Direito ao Esquecimento ────────────────────────────────────────────


@router.post("/lgpd/anonymize/employee/{employee_id}")
async def anonymize_employee_endpoint(
    employee_id: uuid.UUID,
    reason: str = Body(default="Solicitação do titular (Art. 18, LGPD)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles("super_admin", "admin")),
):
    """Anonimiza todos os dados PII de um funcionário (LGPD Art. 18 — Direito ao Esquecimento)."""
    from app.services.anonymization_service import anonymize_employee

    result = await anonymize_employee(
        db=db,
        tenant_id=current_user.tenant_id,
        employee_id=employee_id,
        reason=reason,
        requested_by=current_user.id,
    )
    return result
