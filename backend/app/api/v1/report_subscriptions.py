"""
Endpoints para gerenciar subscricoes de relatorios executivos por email.

Rotas:
- GET    /api/v1/report-subscriptions           → lista subscricoes do tenant
- POST   /api/v1/report-subscriptions           → cria subscricao
- PATCH  /api/v1/report-subscriptions/{id}      → atualiza
- DELETE /api/v1/report-subscriptions/{id}      → remove
- POST   /api/v1/report-subscriptions/{id}/send-now → envia agora (assincrono)
- POST   /api/v1/report-subscriptions/preview   → preview HTML sem enviar
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.report_subscription import ReportSubscription
from app.models.tenant import Tenant

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════


_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _clean_recipients(raw: list[str]) -> list[str]:
    clean = []
    seen = set()
    for r in raw:
        e = r.strip().lower()
        if not e or e in seen:
            continue
        if not _EMAIL_REGEX.match(e):
            raise ValueError(f"Email invalido: {r}")
        seen.add(e)
        clean.append(e)
    return clean


class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    period: Literal["daily", "weekly", "monthly"] = "weekly"
    recipients: list[str] = Field(min_length=1, max_length=20)
    is_active: bool = True
    send_hour_utc: int = Field(default=11, ge=0, le=23)

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: list[str]) -> list[str]:
        return _clean_recipients(v)


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    period: Optional[Literal["daily", "weekly", "monthly"]] = None
    recipients: Optional[list[str]] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None
    send_hour_utc: Optional[int] = Field(default=None, ge=0, le=23)

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return None
        return _clean_recipients(v)


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    name: str
    period: str
    recipients: list[str]
    is_active: bool
    send_hour_utc: int
    last_sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SendNowRequest(BaseModel):
    extra_recipients: Optional[list[str]] = Field(default=None, max_length=10)

    @field_validator("extra_recipients")
    @classmethod
    def validate_extras(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return None
        return _clean_recipients(v)


class PreviewRequest(BaseModel):
    period: Literal["daily", "weekly", "monthly"] = "weekly"


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> list[ReportSubscription]:
    result = await db.execute(
        select(ReportSubscription)
        .where(ReportSubscription.tenant_id == tenant_id)
        .order_by(ReportSubscription.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    body: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> ReportSubscription:
    sub = ReportSubscription(
        tenant_id=tenant_id,
        name=body.name.strip(),
        period=body.period,
        recipients=body.recipients,
        is_active=body.is_active,
        send_hour_utc=body.send_hour_utc,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    body: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> ReportSubscription:
    sub = await _load_sub(db, subscription_id, tenant_id)

    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        setattr(sub, field, value)

    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    sub = await _load_sub(db, subscription_id, tenant_id)
    await db.delete(sub)
    await db.commit()
    return {"success": True}


@router.post("/{subscription_id}/send-now")
async def send_now(
    subscription_id: uuid.UUID,
    body: SendNowRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """
    Envia o relatorio agora para os destinatarios da subscricao
    (opcionalmente somando extra_recipients).
    """
    sub = await _load_sub(db, subscription_id, tenant_id)
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()

    recipients = list(sub.recipients)
    if body.extra_recipients:
        recipients = list(set(recipients + body.extra_recipients))

    if not recipients:
        raise HTTPException(status_code=400, detail="Subscricao sem destinatarios")

    from app.tasks.executive_report_tasks import send_ad_hoc_report

    result = await send_ad_hoc_report(db, tenant_id, tenant.name, sub.period, recipients)
    return result


@router.post("/preview")
async def preview_report(
    body: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Gera o HTML do relatorio sem enviar email (pra mostrar preview no painel)."""
    from app.services import executive_report_service

    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    data = await executive_report_service.build_report(
        db, tenant_id, tenant.name, period=body.period
    )
    html = executive_report_service.render_report_html(data)
    subject = executive_report_service.render_subject(data)
    return {
        "html": html,
        "subject": subject,
        "kpis": {
            "total_conversations": int(data.total_conversations.current),
            "bot_resolutions": int(data.bot_resolutions.current),
            "auto_resolution_rate": round(data.auto_resolution_rate, 1),
            "avg_satisfaction": data.avg_satisfaction,
            "open_tickets": data.open_tickets,
            "sla_breached": data.sla_breached,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


async def _load_sub(
    db: AsyncSession, sub_id: uuid.UUID, tenant_id: uuid.UUID
) -> ReportSubscription:
    result = await db.execute(
        select(ReportSubscription).where(
            ReportSubscription.id == sub_id,
            ReportSubscription.tenant_id == tenant_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscricao nao encontrada")
    return sub
