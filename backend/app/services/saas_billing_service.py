"""
Cobranca SaaS: gerencia assinaturas mensais dos tenants via Mercado Pago.

Fluxo:
  1. tenant solicita link de pagamento → create_saas_checkout()
  2. MP envia webhook → process_saas_webhook()
  3. Admin consulta status → get_billing_status()
"""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

MP_API_URL = "https://api.mercadopago.com"

PLAN_PRICES: dict[str, float] = {
    "starter": settings.SAAS_PLAN_STARTER_PRICE,
    "pro": settings.SAAS_PLAN_PRO_PRICE,
    "enterprise": 0.0,  # negociado manualmente
}

PLAN_LABELS: dict[str, str] = {
    "starter": "IGS Starter",
    "pro": "IGS Pro",
    "enterprise": "IGS Enterprise",
}


async def create_saas_checkout(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    plan: str = "starter",
) -> dict:
    """Gera link de pagamento MP para mensalidade SaaS do tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"success": False, "message": "Tenant nao encontrado."}

    access_token = settings.MP_ACCESS_TOKEN
    if not access_token:
        return {"success": False, "message": "Mercado Pago nao configurado."}

    price = PLAN_PRICES.get(plan, PLAN_PRICES["starter"])
    if price == 0:
        return {"success": False, "message": "Plano Enterprise e negociado manualmente."}

    external_ref = f"saas_{tenant_id.hex}_{plan}"
    now = datetime.now(timezone.utc)
    label = PLAN_LABELS.get(plan, "IGS")
    ref_month = now.strftime("%m/%Y")

    payload = {
        "items": [
            {
                "id": f"saas_{plan}",
                "title": f"{label} — Mensalidade {ref_month}",
                "description": f"Assinatura IGS plano {label.upper()} ref. {ref_month}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": price,
            }
        ],
        "payer": {
            "name": tenant.name,
        },
        "external_reference": external_ref,
        "payment_methods": {
            "installments": 1,
        },
        "expiration_date_to": (now + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000-03:00"),
        "statement_descriptor": "IGS SAAS",
    }

    if settings.SAAS_BILLING_NOTIFICATION_URL:
        payload["notification_url"] = settings.SAAS_BILLING_NOTIFICATION_URL

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{MP_API_URL}/checkout/preferences",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code not in (200, 201):
            logger.error("MP saas checkout error %d: %s", resp.status_code, resp.text[:200])
            return {"success": False, "message": "Erro ao gerar link de pagamento SaaS."}

        data = resp.json()
        return {
            "success": True,
            "checkout_url": data.get("init_point", ""),
            "sandbox_url": data.get("sandbox_init_point", ""),
            "preference_id": data.get("id", ""),
            "plan": plan,
            "amount": str(price),
            "tenant_name": tenant.name,
        }

    except Exception as exc:
        logger.error("Erro ao criar checkout saas: %s", exc)
        return {"success": False, "message": "Erro ao gerar pagamento."}


async def process_saas_webhook(db: AsyncSession, payment_id: str) -> dict:
    """Consulta pagamento MP e ativa/suspende tenant conforme resultado."""
    access_token = settings.MP_ACCESS_TOKEN
    if not access_token:
        return {"success": False}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{MP_API_URL}/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code != 200:
            return {"success": False, "message": "Erro ao consultar pagamento."}

        data = resp.json()
        status = data.get("status", "")
        external_ref = data.get("external_reference", "")

        if not external_ref or not external_ref.startswith("saas_"):
            return {"success": False, "message": "Referencia nao e SaaS."}

        # saas_{tenant_hex}_{plan}
        parts = external_ref.split("_", 2)
        if len(parts) < 3:
            return {"success": False, "message": "Referencia invalida."}

        tenant_hex = parts[1]
        plan = parts[2]

        try:
            tenant_id = uuid.UUID(tenant_hex)
        except ValueError:
            return {"success": False, "message": "tenant_id invalido."}

        if status == "approved":
            await db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(is_active=True, plan=plan)
            )
            await db.commit()
            logger.info("SaaS payment approved: tenant=%s plan=%s", tenant_id, plan)
            return {"success": True, "tenant_id": str(tenant_id), "plan": plan, "status": "active"}

        elif status in ("rejected", "cancelled"):
            await db.execute(
                update(Tenant).where(Tenant.id == tenant_id).values(is_active=False)
            )
            await db.commit()
            logger.warning("SaaS payment rejected: tenant=%s", tenant_id)
            return {"success": True, "tenant_id": str(tenant_id), "status": "suspended"}

        return {"success": True, "status": status}

    except Exception as exc:
        logger.error("Erro ao processar webhook saas: %s", exc)
        return {"success": False, "message": str(exc)}


async def get_billing_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Retorna status de cobrança do tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"found": False}

    plan = tenant.plan or "starter"
    return {
        "found": True,
        "tenant_id": str(tenant_id),
        "tenant_name": tenant.name,
        "plan": plan,
        "is_active": tenant.is_active,
        "monthly_price": PLAN_PRICES.get(plan, PLAN_PRICES["starter"]),
        "plan_label": PLAN_LABELS.get(plan, plan.title()),
    }


def verify_saas_webhook_signature(
    x_signature: str,
    x_request_id: str,
    data_id: str,
) -> bool:
    """Valida assinatura HMAC do webhook MP para pagamentos SaaS."""
    secret = settings.MP_WEBHOOK_SECRET
    if not secret:
        return True

    parts = {}
    for part in x_signature.split(","):
        key, _, value = part.strip().partition("=")
        parts[key] = value

    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")
    if not ts or not v1:
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    computed = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, v1)
