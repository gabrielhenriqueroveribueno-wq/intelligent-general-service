"""
Webhook do WhatsApp Business Cloud API.

GET  /webhook/whatsapp  - Verificação de desafio da Meta
POST /webhook/whatsapp  - Recebe mensagens e atualizações de status
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.models.conversation import Contact, Conversation, Message
from app.models.tenant import Tenant
from app.tasks.message_tasks import process_incoming_message
from app.utils.data_masking import mask_pii
from app.utils.whatsapp_crypto import verify_webhook_signature

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
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
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
                await _handle_incoming_message(db, raw_msg, phone_number_id, contact_name)

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
        await db.execute(update(Message).where(Message.whatsapp_msg_id == msg_id).values(**updates))


async def _handle_incoming_message(
    db: AsyncSession,
    raw_msg: dict,
    phone_number_id: str,
    contact_name: str | None,
):
    """Persiste a mensagem e enfileira o processamento via Celery."""
    msg_type = raw_msg.get("type", "text")
    from_phone = raw_msg.get("from")
    whatsapp_msg_id = raw_msg.get("id")

    supported_types = {"text", "image", "document", "audio", "video", "sticker"}
    if msg_type not in supported_types:
        logger.debug("Tipo de mensagem não suportado: %s", msg_type)
        return

    # Extrai conteúdo conforme tipo
    text_body = ""
    media_id = None
    media_mime_type = None

    if msg_type == "text":
        text_body = raw_msg.get("text", {}).get("body", "").strip()
        if not text_body:
            return
    elif msg_type in ("image", "document", "video", "sticker"):
        media_data = raw_msg.get(msg_type, {})
        media_id = media_data.get("id")
        media_mime_type = media_data.get("mime_type")
        caption = media_data.get("caption", "")
        filename = media_data.get("filename", "")
        text_body = caption or filename or f"[{msg_type}]"
    elif msg_type == "audio":
        # Áudio: notifica usuário que não é suportado ainda
        media_data = raw_msg.get("audio", {})
        media_id = media_data.get("id")
        media_mime_type = media_data.get("mime_type")
        text_body = "[audio]"

    # Encontra o tenant pelo phone_number_id
    tenant_result = await db.execute(
        select(Tenant).where(
            Tenant.whatsapp_phone_number_id == phone_number_id,
            Tenant.is_active,
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
        select(Conversation)
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.contact_id == contact.id,
            Conversation.status.in_(["active", "waiting_agent"]),
        )
        .order_by(Conversation.started_at.desc())
        .limit(1)
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

    # Persiste a mensagem do usuário (com PII mascarado — LGPD)
    message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        sender_type="user",
        content=mask_pii(text_body),
        message_type=msg_type if msg_type in ("image", "document", "audio", "video") else "text",
        whatsapp_msg_id=whatsapp_msg_id,
        whatsapp_media_id=media_id,
        media_mime_type=media_mime_type,
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

    # Verificação de identidade agora é feita no message_tasks.py
    # (o webhook apenas persiste a mensagem e enfileira para o Celery)

    return contact
