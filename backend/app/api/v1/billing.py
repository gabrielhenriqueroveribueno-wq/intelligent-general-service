"""
Rotas de cobranca SaaS.

GET  /billing/status         — status do plano do tenant atual
POST /billing/checkout       — gera link de pagamento avulso (one-shot)
POST /billing/subscribe      — cria assinatura recorrente via pre_approval MP
POST /billing/webhook        — recebe notificacoes do Mercado Pago
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import saas_billing_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
async def billing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna status de cobrança do tenant autenticado."""
    status = await saas_billing_service.get_billing_status(db, current_user.tenant_id)
    if not status["found"]:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return status


@router.post("/checkout")
async def create_checkout(
    plan: str = "starter",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gera link de pagamento Mercado Pago para o plano escolhido."""
    if plan not in ("starter", "pro"):
        raise HTTPException(status_code=400, detail="Plano inválido. Use 'starter' ou 'pro'.")

    result = await saas_billing_service.create_saas_checkout(db, current_user.tenant_id, plan)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result.get("message", "Erro ao gerar checkout"))
    return result


@router.post("/subscribe")
async def create_subscription(
    plan: str = "starter",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria assinatura recorrente via Mercado Pago pre_approval."""
    if plan not in ("starter", "pro"):
        raise HTTPException(status_code=400, detail="Plano inválido. Use 'starter' ou 'pro'.")

    result = await saas_billing_service.create_recurring_subscription(
        db, current_user.tenant_id, plan
    )
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result.get("message", "Erro ao criar assinatura"))
    return result


@router.post("/webhook")
async def billing_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str = Header(default="", alias="x-signature"),
    x_request_id: str = Header(default="", alias="x-request-id"),
):
    """
    Webhook do Mercado Pago para pagamentos SaaS.
    MP envia: POST /billing/webhook?topic=payment&id=PAYMENT_ID
    """
    params = dict(request.query_params)
    topic = params.get("topic", params.get("type", ""))
    data_id = params.get("id", params.get("data.id", ""))

    if x_signature and data_id:
        if not saas_billing_service.verify_saas_webhook_signature(
            x_signature, x_request_id, data_id
        ):
            logger.warning("Webhook SaaS assinatura invalida")
            raise HTTPException(status_code=401, detail="Assinatura inválida")

    if topic in ("payment", "merchant_order") and data_id:
        result = await saas_billing_service.process_saas_webhook(db, data_id)
        logger.info("SaaS webhook processado: topic=%s id=%s result=%s", topic, data_id, result)

    elif topic in ("preapproval", "subscription_preapproval") and data_id:
        result = await saas_billing_service.process_preapproval_webhook(db, data_id)
        logger.info("Pre_approval webhook: id=%s result=%s", data_id, result)

    return {"received": True}
