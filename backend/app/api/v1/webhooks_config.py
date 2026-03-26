"""
API para gerenciar endpoints de webhook de saída por tenant.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.webhook import WebhookDelivery, WebhookEndpoint

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────

class WebhookEndpointCreate(BaseModel):
    url: HttpUrl
    secret: Optional[str] = None
    description: Optional[str] = None
    events: str = "*"  # "*" ou lista separada por vírgula


class WebhookEndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    description: Optional[str]
    events: str
    is_active: bool

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    attempt: int
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    delivered_at: str

    model_config = {"from_attributes": True}


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("", response_model=list[WebhookEndpointResponse])
async def list_endpoints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == current_user.tenant_id
        ).order_by(WebhookEndpoint.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    body: WebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = WebhookEndpoint(
        tenant_id=current_user.tenant_id,
        url=str(body.url),
        secret=body.secret,
        description=body.description,
        events=body.events,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


@router.patch("/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_endpoint(
    endpoint_id: uuid.UUID,
    body: WebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.tenant_id == current_user.tenant_id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint não encontrado")

    endpoint.url = str(body.url)
    if body.secret is not None:
        endpoint.secret = body.secret
    if body.description is not None:
        endpoint.description = body.description
    endpoint.events = body.events
    await db.commit()
    await db.refresh(endpoint)
    return endpoint


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.tenant_id == current_user.tenant_id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint não encontrado")
    await db.delete(endpoint)
    await db.commit()


@router.get("/{endpoint_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    endpoint_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verifica propriedade
    ep_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.tenant_id == current_user.tenant_id,
        )
    )
    if not ep_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Endpoint não encontrado")

    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == endpoint_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(limit)
    )
    deliveries = result.scalars().all()
    return [
        WebhookDeliveryResponse(
            id=d.id,
            event_type=d.event_type,
            attempt=d.attempt,
            status_code=d.status_code,
            success=d.success,
            error_message=d.error_message,
            delivered_at=d.delivered_at.isoformat(),
        )
        for d in deliveries
    ]
