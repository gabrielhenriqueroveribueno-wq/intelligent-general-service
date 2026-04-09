"""
Serviço de pagamentos — PIX BR Code e negociação/parcelamento de débitos.

PIX Copia e Cola:
    Gera payload EMV conforme padrão BR Code do Banco Central.
    Ref: https://www.bcb.gov.br/content/estabilidadefinanceira/pix/regulamentoBRCode.pdf

Negociação:
    Permite parcelar boletos pendentes/vencidos com juros configuráveis.
"""

import logging
import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Boleto, InstallmentPlan
from app.models.student import Student

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# PIX BR Code (EMV format)
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_PIX_KEY = ""  # Set via env or tenant config
MERCHANT_NAME = "FACULDADE IGS"
MERCHANT_CITY = "SAO PAULO"


def _tlv(tag: str, value: str) -> str:
    """Encode a TLV (Tag-Length-Value) field for EMV payload."""
    length = f"{len(value):02d}"
    return f"{tag}{length}{value}"


def _crc16_ccitt(payload: str) -> str:
    """CRC16-CCITT checksum for PIX payload validation."""
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def generate_pix_code(
    pix_key: str,
    amount: Decimal,
    txid: str,
    description: str = "",
    merchant_name: str = MERCHANT_NAME,
    merchant_city: str = MERCHANT_CITY,
) -> str:
    """
    Gera PIX Copia e Cola (BR Code estático) conforme especificação EMV do BCB.

    Args:
        pix_key: Chave PIX do recebedor (CPF, CNPJ, email, telefone ou EVP)
        amount: Valor em reais (ex: Decimal("150.00"))
        txid: Identificador da transação (até 25 chars)
        description: Descrição opcional
        merchant_name: Nome do recebedor
        merchant_city: Cidade do recebedor

    Returns:
        String do BR Code pronta para copiar/colar ou gerar QR Code.
    """
    # Merchant Account Information (tag 26)
    gui = _tlv("00", "br.gov.bcb.pix")
    key = _tlv("01", pix_key)
    desc_field = _tlv("02", description[:25]) if description else ""
    merchant_account = _tlv("26", gui + key + desc_field)

    # Amount formatting
    amount_str = f"{amount:.2f}"

    payload_parts = [
        _tlv("00", "01"),  # Payload Format Indicator
        merchant_account,  # Merchant Account Info
        _tlv("52", "0000"),  # Merchant Category Code
        _tlv("53", "986"),  # Transaction Currency (BRL)
        _tlv("54", amount_str),  # Transaction Amount
        _tlv("58", "BR"),  # Country Code
        _tlv("59", merchant_name[:25]),  # Merchant Name
        _tlv("60", merchant_city[:15]),  # Merchant City
        _tlv("62", _tlv("05", txid[:25])),  # Additional Data (txid)
    ]

    payload = "".join(payload_parts)
    # CRC placeholder (tag 63, length 04)
    payload += "6304"
    crc = _crc16_ccitt(payload)
    return payload + crc


# ══════════════════════════════════════════════════════════════════════════════
# PIX Service Functions
# ══════════════════════════════════════════════════════════════════════════════


async def generate_pix_for_boleto(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    boleto_id: uuid.UUID,
    pix_key: str = "",
) -> dict:
    """
    Gera código PIX para um boleto existente.

    Returns:
        dict com pix_code, txid, amount, e status.
    """
    result = await db.execute(
        select(Boleto).where(
            Boleto.id == boleto_id,
            Boleto.tenant_id == tenant_id,
        )
    )
    boleto = result.scalar_one_or_none()
    if not boleto:
        return {"success": False, "message": "Boleto não encontrado."}

    if boleto.status == "paid":
        return {"success": False, "message": "Este boleto já foi pago."}

    effective_key = pix_key or DEFAULT_PIX_KEY
    if not effective_key:
        return {"success": False, "message": "Chave PIX não configurada para este tenant."}

    txid = f"IGS{boleto.id.hex[:20].upper()}"
    description = f"Mensalidade {boleto.reference_month}"

    code = generate_pix_code(
        pix_key=effective_key,
        amount=boleto.amount,
        txid=txid,
        description=description,
    )

    boleto.pix_code = code
    boleto.pix_txid = txid
    boleto.pix_expiration = date.today() + timedelta(days=3)
    await db.flush()

    return {
        "success": True,
        "pix_code": code,
        "txid": txid,
        "amount": str(boleto.amount),
        "expiration": str(boleto.pix_expiration),
        "message": f"PIX gerado para boleto de {boleto.reference_month}. Valor: R$ {boleto.amount}",
    }


async def generate_pix_for_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    pix_key: str = "",
) -> dict:
    """Gera PIX para o boleto pendente mais antigo do aluno."""
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

    return await generate_pix_for_boleto(db, tenant_id, boleto.id, pix_key)


# ══════════════════════════════════════════════════════════════════════════════
# Negotiation / Installment Service
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_MAX_INSTALLMENTS = 12
DEFAULT_INTEREST_RATE = Decimal("0.02")  # 2% ao mês


async def negotiate_debt(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    num_installments: int,
    interest_rate: Optional[Decimal] = None,
    reason: str = "Negociação via WhatsApp",
    negotiated_by: str = "ai",
) -> dict:
    """
    Cria plano de parcelamento para todos os boletos pendentes/vencidos do aluno.

    Args:
        num_installments: Número de parcelas (2-12)
        interest_rate: Taxa de juros mensal (default 2%)
        reason: Motivo da negociação
        negotiated_by: "ai" ou user_id

    Returns:
        dict com detalhes do plano de parcelamento.
    """
    if num_installments < 2 or num_installments > DEFAULT_MAX_INSTALLMENTS:
        return {
            "success": False,
            "message": f"Número de parcelas deve ser entre 2 e {DEFAULT_MAX_INSTALLMENTS}.",
        }

    # Busca boletos pendentes/vencidos
    result = await db.execute(
        select(Boleto).where(
            Boleto.tenant_id == tenant_id,
            Boleto.student_id == student_id,
            Boleto.status.in_(["pending", "overdue"]),
            Boleto.installment_plan_id.is_(None),
        )
    )
    pending_boletos = list(result.scalars().all())
    if not pending_boletos:
        return {"success": False, "message": "Nenhum débito pendente para negociar."}

    original_total = sum(b.amount for b in pending_boletos)
    rate = interest_rate if interest_rate is not None else DEFAULT_INTEREST_RATE

    # Cálculo: juros simples sobre o total
    total_with_interest = original_total * (1 + rate * num_installments)
    total_with_interest = total_with_interest.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    installment_amount = (total_with_interest / num_installments).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Cria o plano
    plan = InstallmentPlan(
        tenant_id=tenant_id,
        student_id=student_id,
        original_amount=original_total,
        total_amount=total_with_interest,
        num_installments=num_installments,
        interest_rate=rate,
        status="active",
        negotiation_reason=reason,
        negotiated_by=negotiated_by,
        original_boleto_ids=[str(b.id) for b in pending_boletos],
    )
    db.add(plan)
    await db.flush()

    # Marca boletos originais como negociados
    for boleto in pending_boletos:
        boleto.status = "negotiated"

    # Cria novos boletos parcelados
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    student_name = student.full_name if student else "Aluno"

    today = date.today()
    new_boletos = []
    for i in range(1, num_installments + 1):
        due = today + timedelta(days=30 * i)
        new_boleto = Boleto(
            tenant_id=tenant_id,
            student_id=student_id,
            reference_month=f"{due.year}-{due.month:02d}",
            amount=installment_amount,
            due_date=due,
            status="pending",
            installment_plan_id=plan.id,
            installment_number=i,
        )
        db.add(new_boleto)
        new_boletos.append(new_boleto)

    await db.flush()

    return {
        "success": True,
        "plan_id": str(plan.id),
        "student_name": student_name,
        "original_amount": str(original_total),
        "total_amount": str(total_with_interest),
        "num_installments": num_installments,
        "installment_amount": str(installment_amount),
        "interest_rate": str(rate),
        "boletos_negotiated": len(pending_boletos),
        "message": (
            f"Negociação aprovada para {student_name}! "
            f"Débito de R$ {original_total} parcelado em {num_installments}x "
            f"de R$ {installment_amount} (juros de {rate * 100:.1f}%/mês). "
            f"Total: R$ {total_with_interest}."
        ),
    }


async def get_installment_plan(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Optional[dict]:
    """Retorna o plano de parcelamento ativo do aluno, se houver."""
    result = await db.execute(
        select(InstallmentPlan).where(
            InstallmentPlan.tenant_id == tenant_id,
            InstallmentPlan.student_id == student_id,
            InstallmentPlan.status == "active",
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return None

    # Busca parcelas do plano
    boletos_result = await db.execute(
        select(Boleto)
        .where(Boleto.installment_plan_id == plan.id)
        .order_by(Boleto.installment_number)
    )
    boletos = list(boletos_result.scalars().all())

    paid = sum(1 for b in boletos if b.status == "paid")
    pending = sum(1 for b in boletos if b.status in ("pending", "overdue"))

    return {
        "plan_id": str(plan.id),
        "original_amount": str(plan.original_amount),
        "total_amount": str(plan.total_amount),
        "num_installments": plan.num_installments,
        "paid_installments": paid,
        "pending_installments": pending,
        "installments": [
            {
                "number": b.installment_number,
                "amount": str(b.amount),
                "due_date": str(b.due_date) if b.due_date else None,
                "status": b.status,
            }
            for b in boletos
        ],
    }
