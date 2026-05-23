# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
webhook_delivery_service.py
Enfileira e entrega eventos para endpoints externos cadastrados pelos tenants.
Usa assinatura HMAC-SHA256 no header X-IGS-Signature para validação pelo receptor.
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)

DELIVERY_TIMEOUT = 10  # segundos


async def dispatch_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_type: str,
    payload: dict,
) -> None:
    """
    Busca todos os endpoints ativos do tenant que subscrevem o evento
    e enfileira uma tarefa Celery para cada um.
    """
    from app.tasks.webhook_tasks import deliver_webhook_task

    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active,
        )
    )
    endpoints = result.scalars().all()

    for endpoint in endpoints:
        subscribed = endpoint.events.split(",") if endpoint.events != "*" else ["*"]
        if "*" not in subscribed and event_type not in subscribed:
            continue

        # Cria registro de delivery pendente
        delivery = WebhookDelivery(
            endpoint_id=endpoint.id,
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
        )
        db.add(delivery)
        await db.flush()  # obtém o ID antes de enfileirar

        deliver_webhook_task.apply_async(
            args=[str(delivery.id)],
            countdown=0,
        )
        logger.debug(
            "Webhook enfileirado: endpoint=%s event=%s delivery=%s",
            endpoint.id,
            event_type,
            delivery.id,
        )


async def send_delivery(db: AsyncSession, delivery_id: uuid.UUID) -> bool:
    """
    Executa a requisição HTTP para o endpoint e registra o resultado.
    Retorna True em caso de sucesso (2xx).
    """
    result = await db.execute(select(WebhookDelivery).where(WebhookDelivery.id == delivery_id))
    delivery = result.scalar_one_or_none()
    if not delivery:
        logger.error("WebhookDelivery não encontrado: %s", delivery_id)
        return False

    ep_result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.id == delivery.endpoint_id)
    )
    endpoint = ep_result.scalar_one_or_none()
    if not endpoint or not endpoint.is_active:
        return False

    body = json.dumps(
        {
            "id": str(delivery.id),
            "event": delivery.event_type,
            "tenant_id": str(delivery.tenant_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": delivery.payload,
        },
        ensure_ascii=False,
    )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "IGS-Webhook/1.0",
        "X-IGS-Event": delivery.event_type,
        "X-IGS-Delivery": str(delivery.id),
    }

    if endpoint.secret:
        sig = hmac.new(
            endpoint.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-IGS-Signature"] = f"sha256={sig}"

    success = False
    try:
        async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT) as client:
            resp = await client.post(endpoint.url, content=body, headers=headers)
            delivery.status_code = resp.status_code
            delivery.response_body = resp.text[:1000]
            success = resp.is_success
            delivery.success = success
    except Exception as exc:
        delivery.error_message = str(exc)
        logger.warning("Erro ao entregar webhook delivery=%s: %s", delivery_id, exc)

    delivery.delivered_at = datetime.now(timezone.utc)
    await db.commit()
    return success
