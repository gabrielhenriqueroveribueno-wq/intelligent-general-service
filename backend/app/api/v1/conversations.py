import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_tenant_id, require_roles
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    AgentMessageCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.utils.exceptions import NotFoundError

router = APIRouter()


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

    query = query.offset((page - 1) * size).limit(size).order_by(Conversation.last_message_at.desc())
    result = await db.execute(query)
    convs = result.scalars().all()

    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in convs],
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

    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msgs_result.scalars().all()

    detail = ConversationDetailResponse.model_validate(conv)
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
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return ConversationResponse.model_validate(result.scalar_one())


@router.post("/{conversation_id}/close", response_model=ConversationResponse)
async def close_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    from datetime import datetime, timezone

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        .values(status="closed", closed_at=datetime.now(timezone.utc))
    )
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return ConversationResponse.model_validate(result.scalar_one())


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_agent_message(
    conversation_id: uuid.UUID,
    body: AgentMessageCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    """Agente envia mensagem via WhatsApp para o contato."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.tenant_id == tenant_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversa")

    # Aqui enviaria via WhatsApp API em produção (usando tenant config)
    msg = Message(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        sender_type="agent",
        content=body.content,
    )
    db.add(msg)
    await db.flush()
    return MessageResponse.model_validate(msg)
