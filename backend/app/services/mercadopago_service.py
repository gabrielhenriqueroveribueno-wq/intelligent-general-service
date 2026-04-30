"""
Integracaoo com Mercado Pago Checkout Pro.

Gera links de pagamento (PIX + cartao) e processa webhooks de confirmacao.
Docs: https://www.mercadopago.com.br/developers/pt/docs/checkout-pro
"""

import hashlib
import hmac
import logging
import uuid

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.billing import Boleto
from app.models.student import Student

logger = logging.getLogger(__name__)

MP_API_URL = "https://api.mercadopago.com"


async def create_checkout_preference(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    boleto_id: uuid.UUID,
    student_name: str,
    notification_url: str | None = None,
) -> dict:
    """
    Cria uma preferencia de pagamento no Mercado Pago (Checkout Pro).
    Retorna link de pagamento que aceita PIX, cartao e boleto.
    """
    result = await db.execute(
        select(Boleto).where(Boleto.id == boleto_id, Boleto.tenant_id == tenant_id)
    )
    boleto = result.scalar_one_or_none()
    if not boleto:
        return {"success": False, "message": "Boleto nao encontrado."}

    if boleto.status == "paid":
        return {"success": False, "message": "Este boleto ja foi pago."}

    access_token = settings.MP_ACCESS_TOKEN
    if not access_token:
        return {"success": False, "message": "Mercado Pago nao configurado."}

    external_ref = f"igs_{boleto.id.hex}"

    payload = {
        "items": [
            {
                "id": str(boleto.id),
                "title": f"Mensalidade {boleto.reference_month} - Faculdade Anchieta",
                "description": f"Pagamento referente a {boleto.reference_month}",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(boleto.amount),
            }
        ],
        "payer": {
            "name": student_name.split()[0] if student_name else "Aluno",
            "surname": " ".join(student_name.split()[1:]) if student_name and len(student_name.split()) > 1 else "",
        },
        "external_reference": external_ref,
        "payment_methods": {
            "excluded_payment_types": [],
            "installments": 6,
        },
        "statement_descriptor": "FACULDADE IGS",
    }

    if notification_url:
        payload["notification_url"] = notification_url

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{MP_API_URL}/checkout/preferences",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )

        if resp.status_code not in (200, 201):
            logger.error("MP preference error %d: %s", resp.status_code, resp.text)
            return {"success": False, "message": "Erro ao gerar link de pagamento."}

        data = resp.json()

        # Salva referencia no boleto
        boleto.pix_txid = external_ref
        await db.flush()

        return {
            "success": True,
            "checkout_url": data.get("init_point", ""),
            "sandbox_url": data.get("sandbox_init_point", ""),
            "preference_id": data.get("id", ""),
            "external_reference": external_ref,
            "amount": str(boleto.amount),
            "message": (
                f"Link de pagamento gerado para mensalidade de *{boleto.reference_month}*.\n"
                f"Valor: *R$ {boleto.amount}*\n"
                f"Aceita PIX, cartao de credito/debito e boleto."
            ),
        }

    except httpx.TimeoutException:
        logger.error("Timeout ao criar preferencia MP")
        return {"success": False, "message": "Timeout ao gerar link de pagamento."}
    except Exception as exc:
        logger.error("Erro ao criar preferencia MP: %s", exc)
        return {"success": False, "message": "Erro ao gerar link de pagamento."}


async def create_checkout_for_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    notification_url: str | None = None,
) -> dict:
    """Cria checkout para o boleto pendente mais antigo do aluno."""
    result = await db.execute(
        select(Boleto)
        .where(
            Boleto.tenant_id == tenant_id,
            Boleto.student_id == student_id,
            Boleto.status.in_(["pending", "overdue"]),
        )
        .order_by(Boleto.due_date.asc())
        .limit(1)
    )
    boleto = result.scalar_one_or_none()
    if not boleto:
        return {"success": False, "message": "Nenhum boleto pendente encontrado."}

    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    student_name = student.full_name if student else "Aluno"

    return await create_checkout_preference(
        db, tenant_id, boleto.id, student_name, notification_url
    )


async def process_payment_webhook(db: AsyncSession, payment_id: str) -> dict:
    """
    Consulta pagamento no MP e atualiza status do boleto.
    Chamado pelo webhook quando MP notifica pagamento.
    """
    access_token = settings.MP_ACCESS_TOKEN
    if not access_token:
        return {"success": False, "message": "MP nao configurado."}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{MP_API_URL}/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code != 200:
            logger.error("Erro ao consultar pagamento MP %s: %d", payment_id, resp.status_code)
            return {"success": False, "message": "Erro ao consultar pagamento."}

        data = resp.json()
        status = data.get("status", "")
        external_ref = data.get("external_reference", "")
        payment_method = data.get("payment_method_id", "")
        amount = data.get("transaction_amount", 0)

        if not external_ref or not external_ref.startswith("igs_"):
            return {"success": False, "message": "Referencia externa invalida."}

        boleto_hex = external_ref[4:]  # Remove "igs_"

        try:
            boleto_uuid = uuid.UUID(boleto_hex)
        except ValueError:
            return {"success": False, "message": "ID do boleto invalido."}

        if status == "approved":
            await db.execute(
                update(Boleto)
                .where(Boleto.id == boleto_uuid)
                .values(status="paid")
            )
            await db.commit()

            logger.info(
                "Pagamento confirmado: boleto=%s metodo=%s valor=%.2f",
                boleto_uuid, payment_method, amount,
            )

            return {
                "success": True,
                "boleto_id": str(boleto_uuid),
                "status": "paid",
                "payment_method": payment_method,
                "amount": str(amount),
                "message": "Pagamento confirmado com sucesso!",
            }

        elif status in ("pending", "in_process"):
            logger.info("Pagamento pendente: boleto=%s status=%s", boleto_uuid, status)
            return {"success": True, "status": status, "message": "Pagamento em processamento."}

        elif status in ("rejected", "cancelled"):
            logger.warning("Pagamento recusado: boleto=%s status=%s", boleto_uuid, status)
            return {"success": False, "status": status, "message": "Pagamento recusado ou cancelado."}

        return {"success": True, "status": status}

    except Exception as exc:
        logger.error("Erro ao processar webhook MP: %s", exc)
        return {"success": False, "message": str(exc)}


def verify_webhook_signature(
    x_signature: str,
    x_request_id: str,
    data_id: str,
) -> bool:
    """Valida assinatura HMAC do webhook do Mercado Pago."""
    secret = settings.MP_WEBHOOK_SECRET
    if not secret:
        return True  # Skip verification if no secret configured

    # Parse x_signature: "ts=xxx,v1=xxx"
    parts = {}
    for part in x_signature.split(","):
        key, _, value = part.strip().partition("=")
        parts[key] = value

    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")

    if not ts or not v1:
        return False

    # Build manifest
    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"

    # HMAC-SHA256
    computed = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, v1)
