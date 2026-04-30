"""
Testes do fluxo de pesquisa de satisfacao (feedback).

Cobre:
- Reconhecimento de gatilhos de despedida
- Salvamento da nota no banco
- Webhook reaproveita conversa em status awaiting_feedback (regressao!)
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Contact, Conversation, Message
from app.models.satisfaction import SatisfactionSurvey
from app.models.tenant import Tenant

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures: cenario de feedback
# ══════════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def contact_verified(db: AsyncSession, test_tenant: Tenant) -> Contact:
    contact = Contact(
        tenant_id=test_tenant.id,
        phone_number="5511999991234",
        name="Lucas Silva",
        contact_type="student",
        is_verified=True,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def conversation_awaiting_feedback(
    db: AsyncSession, test_tenant: Tenant, contact_verified: Contact
) -> Conversation:
    conv = Conversation(
        tenant_id=test_tenant.id,
        contact_id=contact_verified.id,
        status="awaiting_feedback",
        channel="whatsapp",
        started_at=datetime.now(timezone.utc),
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    # Bot pediu nota nessa conversa
    bot_msg = Message(
        tenant_id=test_tenant.id,
        conversation_id=conv.id,
        sender_type="bot",
        content="Me da uma nota de 1 a 5 pro atendimento? 1 = ruim, 5 = excelente",
    )
    db.add(bot_msg)
    await db.commit()
    return conv


# ══════════════════════════════════════════════════════════════════════════════
# Detector de despedida (regex puro, sem IA)
# ══════════════════════════════════════════════════════════════════════════════


# Estes triggers sao copiados do message_tasks.py — qualquer mudanca la deve
# refletir aqui. O teste serve como contrato.
FAREWELL_TRIGGERS = (
    "não",
    "nao",
    "não obrigado",
    "nao obrigado",
    "era só isso",
    "era so isso",
    "obrigado",
    "obrigada",
    "valeu",
    "tchau",
    "só isso",
    "so isso",
    "tá bom",
    "ta bom",
    "até mais",
    "ate mais",
    "nada mais",
    "é isso",
    "e isso",
    "só isso mesmo",
    "so isso mesmo",
    "não preciso",
    "nao preciso",
    "era isso",
    "brigado",
    "brigada",
    "flw",
    "falou",
    "vlw",
    "tmj",
)


def _matches_farewell(msg: str) -> bool:
    msg_lower = msg.strip().lower().rstrip("!.,;")
    return any(t in msg_lower for t in FAREWELL_TRIGGERS)


@pytest.mark.parametrize(
    "message,should_match",
    [
        # Frases curtas
        ("não", True),
        ("Não, obrigado!", True),
        ("Era só isso, obrigado", True),
        ("Era só isso mesmo, obrigado!", True),
        ("Valeu, tchau", True),
        ("brigado", True),
        ("flw", True),
        # Mensagens normais nao devem disparar
        ("quero ver minhas notas", False),
        ("quanto e a mensalidade", False),
        ("preciso falar com alguem", False),
    ],
)
def test_farewell_detector(message: str, should_match: bool):
    assert _matches_farewell(message) is should_match


# ══════════════════════════════════════════════════════════════════════════════
# Salvamento da nota no banco
# ══════════════════════════════════════════════════════════════════════════════


async def _save_feedback_compat(db, tenant_id, conversation_id, contact_id, score: int):
    """
    Versao compativel com SQLite do _save_feedback (cria SatisfactionSurvey
    setando created_at explicitamente em vez de depender de server_default='now()'
    que so funciona em PostgreSQL).
    """
    survey = SatisfactionSurvey(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        contact_id=contact_id,
        score=score,
        responder_type="bot",
        survey_sent_at=datetime.now(timezone.utc),
        responded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(survey)


@pytest.mark.asyncio
async def test_save_feedback_persists_score(
    db: AsyncSession,
    test_tenant: Tenant,
    contact_verified: Contact,
    conversation_awaiting_feedback: Conversation,
):
    await _save_feedback_compat(
        db,
        test_tenant.id,
        conversation_awaiting_feedback.id,
        contact_verified.id,
        score=5,
    )
    await db.commit()

    surveys = (
        (
            await db.execute(
                select(SatisfactionSurvey).where(
                    SatisfactionSurvey.conversation_id == conversation_awaiting_feedback.id
                )
            )
        )
        .scalars()
        .all()
    )

    assert len(surveys) == 1
    assert surveys[0].score == 5
    assert surveys[0].tenant_id == test_tenant.id


@pytest.mark.asyncio
async def test_save_feedback_records_responder_type_bot(
    db: AsyncSession,
    test_tenant: Tenant,
    contact_verified: Contact,
    conversation_awaiting_feedback: Conversation,
):
    await _save_feedback_compat(
        db,
        test_tenant.id,
        conversation_awaiting_feedback.id,
        contact_verified.id,
        score=3,
    )
    await db.commit()

    survey = (
        await db.execute(
            select(SatisfactionSurvey).where(
                SatisfactionSurvey.conversation_id == conversation_awaiting_feedback.id
            )
        )
    ).scalar_one()
    assert survey.responder_type == "bot"


# ══════════════════════════════════════════════════════════════════════════════
# Reaproveitamento de conversa em awaiting_feedback (regressao do bug fixado hoje)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_query_awaiting_feedback_conversations(
    db: AsyncSession,
    test_tenant: Tenant,
    contact_verified: Contact,
    conversation_awaiting_feedback: Conversation,
):
    """
    Webhook deve achar conversas em status awaiting_feedback ao receber
    nova mensagem (a nota '5'), em vez de criar conversa nova.
    Essa query eh exatamente a do webhook.py.
    """
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.tenant_id == test_tenant.id,
            Conversation.contact_id == contact_verified.id,
            Conversation.status.in_(["active", "waiting_agent", "awaiting_feedback"]),
        )
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.id == conversation_awaiting_feedback.id
    assert found.status == "awaiting_feedback"


@pytest.mark.asyncio
async def test_old_query_would_create_duplicate_conversation(
    db: AsyncSession,
    test_tenant: Tenant,
    contact_verified: Contact,
    conversation_awaiting_feedback: Conversation,
):
    """
    Snapshot do bug antigo: a query SEM 'awaiting_feedback' nao acharia a conversa
    e o webhook criaria uma nova — exatamente o bug que resolvemos.
    Este teste documenta o comportamento incorreto pra evitar regressao.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.tenant_id == test_tenant.id,
            Conversation.contact_id == contact_verified.id,
            Conversation.status.in_(["active", "waiting_agent"]),  # SEM awaiting_feedback
        )
    )
    found = result.scalar_one_or_none()
    assert found is None  # confirma que sem o fix nao acharia
