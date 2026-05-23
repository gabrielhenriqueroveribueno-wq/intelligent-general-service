# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Serviço de aprendizado da IA com tickets resolvidos.

Indexa resoluções de tickets para consulta futura, permitindo
que a IA sugira soluções baseadas em casos anteriores.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.ticket import Ticket
from app.models.ticket_learning import TicketResolution
from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)


async def index_resolved_ticket(db: AsyncSession, ticket_id: UUID) -> TicketResolution | None:
    """
    Quando um ticket é fechado, extrai a conversa completa,
    usa IA para gerar um resumo e salva em ticket_resolutions.
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return None

    # Busca mensagens da conversa associada
    conversation_messages: list[str] = []
    if ticket.conversation_id:
        msgs_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == ticket.conversation_id)
            .order_by(Message.created_at)
            .limit(50)
        )
        for msg in msgs_result.scalars().all():
            role = "Usuário" if msg.sender_type == "user" else "Bot"
            conversation_messages.append(f"{role}: {msg.content[:300]}")

    conv_text = "\n".join(conversation_messages) if conversation_messages else "Sem conversa."

    # Usa IA para gerar resumo estruturado
    try:
        ai_result = await ai_complete(
            system=(
                "Analise a conversa de suporte abaixo e retorne um resumo estruturado.\n"
                "Formato:\n"
                "CATEGORIA: (uma palavra: matricula, boleto, nota, frequencia, documento, rh, geral)\n"
                "PROBLEMA: (resumo em 1 frase)\n"
                "SOLUCAO: (resumo em 1-2 frases)\n"
                "TAGS: (palavras-chave separadas por virgula)\n"
                "RESUMO_IA: (texto curto para matching de similaridade)"
            ),
            message=conv_text,
            max_tokens=500,
        )
        raw = ai_result.text
    except Exception as e:
        logger.warning("Erro ao gerar resumo com IA: %s", e)
        raw = ""

    # Parse do resumo
    category = "geral"
    problem = ticket.subject or ""
    solution = ""
    tags: list[str] = []
    summary = ""

    for line in raw.split("\n"):
        line = line.strip()
        if line.upper().startswith("CATEGORIA:"):
            category = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("PROBLEMA:"):
            problem = line.split(":", 1)[1].strip()
        elif line.upper().startswith("SOLUCAO:") or line.upper().startswith("SOLUÇÃO:"):
            solution = line.split(":", 1)[1].strip()
        elif line.upper().startswith("TAGS:"):
            tags = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
        elif line.upper().startswith("RESUMO_IA:"):
            summary = line.split(":", 1)[1].strip()

    # Calcula tempo de resolução
    resolution_seconds = None
    if ticket.resolved_at and ticket.created_at:
        delta = ticket.resolved_at - ticket.created_at
        resolution_seconds = int(delta.total_seconds())

    # Verifica satisfação na conversa
    satisfaction = None
    if ticket.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == ticket.conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if conv and conv.satisfaction_score:
            satisfaction = conv.satisfaction_score

    resolution = TicketResolution(
        tenant_id=ticket.tenant_id,
        ticket_id=ticket.id,
        conversation_id=ticket.conversation_id,
        problem_category=category,
        problem_description=problem,
        resolution_description=solution or "Resolvido pelo sistema.",
        resolution_steps={},
        resolution_type="auto",
        satisfaction_score=satisfaction,
        resolution_time_seconds=resolution_seconds,
        tags=tags or None,
        ai_embedding_summary=summary or problem,
        times_used_as_reference=0,
    )
    db.add(resolution)
    await db.flush()
    return resolution


async def find_similar_resolutions(
    db: AsyncSession,
    tenant_id: UUID,
    problem_description: str,
    limit: int = 5,
) -> list[TicketResolution]:
    """
    Busca resoluções similares usando ILIKE em problem_description,
    tags e ai_embedding_summary.
    """
    keywords = [w for w in problem_description.split() if len(w) > 3][:5]
    if not keywords:
        return []

    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(TicketResolution.problem_description.ilike(pattern))
        conditions.append(TicketResolution.ai_embedding_summary.ilike(pattern))

    stmt = (
        select(TicketResolution)
        .where(
            TicketResolution.tenant_id == tenant_id,
            or_(*conditions),
        )
        .order_by(
            TicketResolution.satisfaction_score.desc().nulls_last(),
            TicketResolution.times_used_as_reference.desc(),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    resolutions = list(result.scalars().all())

    # Incrementa counter de uso
    if resolutions:
        ids = [r.id for r in resolutions]
        await db.execute(
            update(TicketResolution)
            .where(TicketResolution.id.in_(ids))
            .values(times_used_as_reference=TicketResolution.times_used_as_reference + 1)
        )

    return resolutions


async def get_resolution_stats(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
    """Estatísticas de resoluções indexadas."""
    base = select(TicketResolution).where(TicketResolution.tenant_id == tenant_id)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    avg_satisfaction_result = await db.execute(
        select(func.avg(TicketResolution.satisfaction_score)).where(
            TicketResolution.tenant_id == tenant_id,
            TicketResolution.satisfaction_score.is_not(None),
        )
    )
    avg_satisfaction = avg_satisfaction_result.scalar()

    avg_time_result = await db.execute(
        select(func.avg(TicketResolution.resolution_time_seconds)).where(
            TicketResolution.tenant_id == tenant_id,
            TicketResolution.resolution_time_seconds.is_not(None),
        )
    )
    avg_time = avg_time_result.scalar()

    # Top categorias
    cat_result = await db.execute(
        select(
            TicketResolution.problem_category,
            func.count().label("count"),
        )
        .where(TicketResolution.tenant_id == tenant_id)
        .group_by(TicketResolution.problem_category)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_categories = [{"category": row[0], "count": row[1]} for row in cat_result.all()]

    return {
        "total_resolutions": total,
        "avg_satisfaction": round(float(avg_satisfaction), 2) if avg_satisfaction else None,
        "avg_resolution_time_seconds": round(float(avg_time), 1) if avg_time else None,
        "top_categories": top_categories,
    }
