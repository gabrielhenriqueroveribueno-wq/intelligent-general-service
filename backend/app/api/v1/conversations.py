import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.conversation import Contact, Conversation, Message
from app.schemas.conversation import (
    AgentMessageCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.utils.exceptions import NotFoundError

router = APIRouter()


def _conv_to_response(
    conv: Conversation, contact: Optional[Contact] = None
) -> ConversationResponse:
    """Constrói ConversationResponse enriquecido com dados do contato."""
    data = ConversationResponse.model_validate(conv)
    if contact:
        data.contact_name = contact.name
        data.contact_phone = contact.phone_number
    return data


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    from sqlalchemy import func

    query = select(Conversation).where(Conversation.tenant_id == tenant_id)
    if status:
        query = query.where(Conversation.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = (
        query.offset((page - 1) * size).limit(size).order_by(Conversation.last_message_at.desc())
    )
    result = await db.execute(query)
    convs = result.scalars().all()

    # Carrega contatos em batch para enriquecer a resposta
    contact_ids = list({c.contact_id for c in convs})
    contacts_map: dict[uuid.UUID, Contact] = {}
    if contact_ids:
        ct_result = await db.execute(select(Contact).where(Contact.id.in_(contact_ids)))
        for ct in ct_result.scalars().all():
            contacts_map[ct.id] = ct

    return ConversationListResponse(
        items=[_conv_to_response(c, contacts_map.get(c.contact_id)) for c in convs],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.tenant_id == tenant_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversa")

    ct_result = await db.execute(select(Contact).where(Contact.id == conv.contact_id))
    contact = ct_result.scalar_one_or_none()

    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msgs_result.scalars().all()

    detail = ConversationDetailResponse.model_validate(conv)
    if contact:
        detail.contact_name = contact.name
        detail.contact_phone = contact.phone_number
    detail.messages = [MessageResponse.model_validate(m) for m in messages]
    return detail


@router.post("/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation(
    conversation_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        .values(assigned_agent_id=agent_id, status="active")
    )
    await db.commit()
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one()
    ct_result = await db.execute(select(Contact).where(Contact.id == conv.contact_id))
    return _conv_to_response(conv, ct_result.scalar_one_or_none())


@router.post("/{conversation_id}/close", response_model=ConversationResponse)
async def close_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        .values(status="closed", closed_at=datetime.now(timezone.utc))
    )
    await db.commit()

    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one()
    ct_result = await db.execute(select(Contact).where(Contact.id == conv.contact_id))

    # Notifica painel via WebSocket
    try:
        import json as _json

        import redis.asyncio as aioredis

        from app.config import settings as _settings
        from app.services.ws_manager import REDIS_CHANNEL

        _r = aioredis.from_url(_settings.REDIS_URL, decode_responses=True)
        await _r.publish(
            REDIS_CHANNEL,
            _json.dumps(
                {
                    "type": "conversation_closed",
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(conversation_id),
                }
            ),
        )
        await _r.aclose()
    except Exception:
        pass

    # Dispara webhook de saída
    try:
        from app.services.webhook_delivery_service import dispatch_event

        await dispatch_event(
            db,
            tenant_id,
            "conversation.closed",
            {
                "conversation_id": str(conversation_id),
            },
        )
    except Exception:
        pass

    return _conv_to_response(conv, ct_result.scalar_one_or_none())


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_agent_message(
    conversation_id: uuid.UUID,
    body: AgentMessageCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    """Agente envia mensagem via WhatsApp para o contato."""
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.tenant_id == tenant_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversa")

    # Carrega contato para obter número de telefone
    ct_result = await db.execute(select(Contact).where(Contact.id == conv.contact_id))
    contact = ct_result.scalar_one_or_none()

    # Carrega tenant para obter credenciais WhatsApp
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    # Envia via WhatsApp API se o tenant tiver configuração
    wa_msg_id: Optional[str] = None
    if tenant and tenant.whatsapp_phone_number_id and tenant.whatsapp_token and contact:
        wa_msg_id = await whatsapp_service.send_text_message(
            phone_number_id=tenant.whatsapp_phone_number_id,
            access_token=tenant.whatsapp_token,
            to=contact.phone_number,
            body=body.content,
        )

    msg = Message(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        sender_type="agent",
        content=body.content,
        whatsapp_msg_id=wa_msg_id,
    )
    db.add(msg)

    # Atualiza last_message_at
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(last_message_at=datetime.now(timezone.utc))
    )

    await db.commit()
    await db.refresh(msg)

    # Notifica painel via WebSocket
    try:
        import json as _json

        import redis.asyncio as aioredis

        from app.config import settings as _settings
        from app.services.ws_manager import REDIS_CHANNEL

        _r = aioredis.from_url(_settings.REDIS_URL, decode_responses=True)
        await _r.publish(
            REDIS_CHANNEL,
            _json.dumps(
                {
                    "type": "agent_message",
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(conversation_id),
                    "sender_name": current_user.full_name
                    if hasattr(current_user, "full_name")
                    else "Agente",
                }
            ),
        )
        await _r.aclose()
    except Exception:
        pass

    return MessageResponse.model_validate(msg)
