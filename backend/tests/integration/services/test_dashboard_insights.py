"""Testes do get_dashboard_insights (volume 7d, intents, sentimento, CSAT, custo IA)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.conversation import Contact, Conversation, Message
from app.models.satisfaction import SatisfactionSurvey
from app.services.report_service import get_dashboard_insights


async def _seed(db, tenant_id: uuid.UUID, other_tenant_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    # SQLite nao avalia o server_default now() do TimestampMixin — timestamps explicitos
    ts = {"created_at": now, "updated_at": now}
    contact = Contact(tenant_id=tenant_id, phone_number="5511999990000", **ts)
    other_contact = Contact(tenant_id=other_tenant_id, phone_number="5511999990001", **ts)
    db.add_all([contact, other_contact])
    await db.flush()

    conv = Conversation(tenant_id=tenant_id, contact_id=contact.id, started_at=now, **ts)
    conv_old = Conversation(
        tenant_id=tenant_id, contact_id=contact.id, started_at=now - timedelta(days=40), **ts
    )
    conv_other = Conversation(
        tenant_id=other_tenant_id, contact_id=other_contact.id, started_at=now, **ts
    )
    db.add_all([conv, conv_old, conv_other])
    await db.flush()

    db.add_all(
        [
            Message(
                tenant_id=tenant_id,
                conversation_id=conv.id,
                sender_type="user",
                content="quero meu boleto",
                intent="boleto_query",
                sentiment="positive",
                ai_tokens_used=100,
                **ts,
            ),
            Message(
                tenant_id=tenant_id,
                conversation_id=conv.id,
                sender_type="user",
                content="qual minha nota",
                intent="grade_query",
                sentiment="negative",
                ai_tokens_used=200,
                **ts,
            ),
            Message(
                tenant_id=tenant_id,
                conversation_id=conv.id,
                sender_type="user",
                content="oi",
                intent="greeting",  # conversacional: nao deve aparecer em top_intents
                sentiment="neutral",
                **ts,
            ),
            # Mensagem de OUTRO tenant — nunca pode vazar
            Message(
                tenant_id=other_tenant_id,
                conversation_id=conv_other.id,
                sender_type="user",
                content="other",
                intent="payslip_query",
                sentiment="negative",
                ai_tokens_used=999_999,
                **ts,
            ),
        ]
    )
    db.add(
        SatisfactionSurvey(
            tenant_id=tenant_id,
            conversation_id=conv.id,
            contact_id=contact.id,
            score=4,
            survey_sent_at=now,
            created_at=now,
        )
    )
    await db.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insights_aggregates_and_isolates_tenant(
    async_db, sample_tenant_id, sample_tenant_id_2
):
    await _seed(async_db, sample_tenant_id, sample_tenant_id_2)

    insights = await get_dashboard_insights(async_db, sample_tenant_id)

    # Volume: sempre 7 pontos, hoje com 1 conversa (a antiga fica fora da janela)
    assert len(insights["daily_volume"]) == 7
    assert insights["daily_volume"][-1]["count"] == 1
    assert sum(p["count"] for p in insights["daily_volume"]) == 1

    # Top intents: exclui 'greeting' e nao traz intent de outro tenant
    intents = {i["intent"] for i in insights["top_intents"]}
    assert intents == {"boleto_query", "grade_query"}

    # Sentimento: 1 positivo, 1 neutro, 1 negativo (do tenant certo)
    assert insights["sentiment"] == {"positive": 1, "neutral": 1, "negative": 1}

    # CSAT
    assert insights["csat"]["avg_score"] == 4.0
    assert insights["csat"]["responses"] == 1

    # Custo IA: 300 tokens do tenant (sem os 999k do outro)
    assert insights["ai_cost"]["tokens_month"] == 300
    assert insights["ai_cost"]["budget_usd"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insights_empty_tenant_returns_zeroes(async_db):
    insights = await get_dashboard_insights(async_db, uuid.uuid4())

    assert len(insights["daily_volume"]) == 7
    assert all(p["count"] == 0 for p in insights["daily_volume"])
    assert insights["top_intents"] == []
    assert insights["sentiment"] == {"positive": 0, "neutral": 0, "negative": 0}
    assert insights["csat"] == {"avg_score": 0.0, "responses": 0}
    assert insights["ai_cost"]["tokens_month"] == 0
