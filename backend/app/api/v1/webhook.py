"""
Webhook do WhatsApp Business Cloud API.

GET  /webhook/whatsapp  - Verificação de desafio da Meta
POST /webhook/whatsapp  - Recebe mensagens e atualizações de status
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.conversation import Contact, Conversation, Message
from app.models.tenant import Tenant
from app.tasks.message_tasks import process_incoming_message
from app.utils.whatsapp_crypto import verify_webhook_signature
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Verificação do webhook pela Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook WhatsApp verificado com sucesso")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verificação falhou")


@router.post("/whatsapp", status_code=200)
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Recebe mensagens do WhatsApp e as enfileira para processamento."""
    body_bytes = await request.body()

    # Verifica assinatura HMAC
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.WHATSAPP_APP_SECRET and not verify_webhook_signature(body_bytes, signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

    payload: dict[str, Any] = await request.json()

    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue

            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")

            # Atualização de status (entregue, lido) — apenas registra
            for status_upd in value.get("statuses", []):
                await _handle_status_update(db, status_upd)

            # Mensagens recebidas
            contacts = value.get("contacts", [])
            for raw_msg in value.get("messages", []):
                contact_name = contacts[0]["profile"]["name"] if contacts else None
                await _handle_incoming_message(
                    db, raw_msg, phone_number_id, contact_name
                )

    return {"status": "ok"}


async def _handle_status_update(db: AsyncSession, status_upd: dict):
    """Atualiza status de entrega/leitura de uma mensagem."""
    msg_id = status_upd.get("id")
    new_status = status_upd.get("status")
    if not msg_id or not new_status:
        return

    updates = {}
    if new_status == "delivered":
        updates["is_delivered"] = True
    elif new_status == "read":
        updates["is_read"] = True

    if updates:
        await db.execute(
            update(Message)
            .where(Message.whatsapp_msg_id == msg_id)
            .values(**updates)
        )


async def _handle_incoming_message(
    db: AsyncSession,
    raw_msg: dict,
    phone_number_id: str,
    contact_name: str | None,
):
    """Persiste a mensagem e enfileira o processamento via Celery."""
    # Só processa mensagens de texto por enquanto
    if raw_msg.get("type") != "text":
        logger.debug("Tipo de mensagem não suportado: %s", raw_msg.get("type"))
        return

    text_body = raw_msg.get("text", {}).get("body", "").strip()
    if not text_body:
        return

    from_phone = raw_msg.get("from")
    whatsapp_msg_id = raw_msg.get("id")

    # Encontra o tenant pelo phone_number_id
    tenant_result = await db.execute(
        select(Tenant).where(
            Tenant.whatsapp_phone_number_id == phone_number_id,
            Tenant.is_active == True,
        )
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        logger.warning("Tenant não encontrado para phone_number_id: %s", phone_number_id)
        return

    tenant_id = tenant.id

    # Verifica se é verificação de identidade (RA/matrícula)
    contact = await _get_or_create_contact(db, tenant_id, from_phone, contact_name, text_body)

    # Obtém ou cria conversa ativa
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.contact_id == contact.id,
            Conversation.status.in_(["active", "waiting_agent"]),
        ).order_by(Conversation.started_at.desc()).limit(1)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            contact_id=contact.id,
            context_type=contact.contact_type if contact.contact_type != "unknown" else None,
            last_message_at=datetime.now(timezone.utc),
        )
        db.add(conversation)
        await db.flush()

    # Persiste a mensagem do usuário
    message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        sender_type="user",
        content=text_body,
        whatsapp_msg_id=whatsapp_msg_id,
    )
    db.add(message)

    # Atualiza last_message_at da conversa
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation.id)
        .values(last_message_at=datetime.now(timezone.utc))
    )

    await db.flush()

    # Enfileira no Celery para processamento assíncrono
    process_incoming_message.delay(str(message.id))
    logger.info("Mensagem %s enfileirada para processamento", message.id)


async def _get_or_create_contact(
    db: AsyncSession,
    tenant_id,
    phone: str,
    name: str | None,
    text_body: str,
) -> Contact:
    """Obtém ou cria contato. Tenta verificar identidade pelo texto (RA/matrícula)."""
    result = await db.execute(
        select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.phone_number == phone,
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        contact = Contact(
            tenant_id=tenant_id,
            phone_number=phone,
            name=name,
            contact_type="unknown",
            is_verified=False,
        )
        db.add(contact)
        await db.flush()

    # Tenta verificar pelo RA (ex: "RA123456" ou "123456")
    if not contact.is_verified:
        await _try_verify_contact(db, contact, tenant_id, text_body)

    return contact


async def _try_verify_contact(db: AsyncSession, contact: Contact, tenant_id, text_body: str):
    """Tenta linkar o contato a um aluno ou funcionário pelo identificador."""
    import re

    # Padrão RA: RA seguido de números, ou só números de 4-10 dígitos
    ra_match = re.match(r"^(?:RA\s*)?(\d{4,10})$", text_body.strip(), re.IGNORECASE)
    if ra_match:
        ra = ra_match.group(1)
        from app.models.student import Student
        student_result = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_id,
                Student.registration_number == ra,
            )
        )
        student = student_result.scalar_one_or_none()
        if student:
            contact.student_id = student.id
            contact.contact_type = "student"
            contact.is_verified = True
            contact.name = student.full_name
            return

    # Padrão FUNC: FUNC seguido de números
    func_match = re.match(r"^(?:FUNC\s*)?(\w+)$", text_body.strip(), re.IGNORECASE)
    if func_match:
        func_num = func_match.group(1)
        from app.models.employee import Employee
        emp_result = await db.execute(
            select(Employee).where(
                Employee.tenant_id == tenant_id,
                Employee.employee_number == func_num,
            )
        )
        employee = emp_result.scalar_one_or_none()
        if employee:
            contact.employee_id = employee.id
            contact.contact_type = "employee"
            contact.is_verified = True
            contact.name = employee.full_name
