"""
Testes do servico de fallback offline da IA.

Garantem que quando todos os providers falham, a Billie ainda devolve
respostas razoaveis baseadas em palavras-chave / KB / template generico.
"""

from __future__ import annotations

import pytest

from app.services import ai_fallback

# ══════════════════════════════════════════════════════════════════════════════
# Intent detection
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,expected_intent",
    [
        ("quero ver minhas notas", "grade_query"),
        ("quais minhas faltas?", "attendance_query"),
        ("preciso do meu boleto", "boleto_query"),
        ("qual horario da biblioteca?", "schedule_query"),
        ("quero meu holerite", "payslip_query"),
        ("quero tirar ferias", "vacation_query"),
        ("quero falar com humano", "handoff"),
        ("oi, tudo bem?", "greeting"),
        ("obrigado, tchau", "farewell"),
    ],
)
async def test_fallback_detects_common_intents(message: str, expected_intent: str):
    """O detector deve mapear cada mensagem para o intent correto."""
    detected = ai_fallback._detect_intent(message)
    assert detected == expected_intent, (
        f"Esperava '{expected_intent}' para '{message}', recebeu '{detected}'"
    )

    response = await ai_fallback.generate_fallback_response(user_message=message)
    assert response.text
    assert response.provider_used == "offline_fallback"


@pytest.mark.asyncio
async def test_fallback_personalizes_with_contact_name():
    response = await ai_fallback.generate_fallback_response(
        user_message="quero ver minhas notas",
        contact_name="Lucas Silva",
    )
    assert "Lucas" in response.text


@pytest.mark.asyncio
async def test_fallback_handoff_includes_command():
    """Mensagens de pedido humano devem incluir [HANDOFF] pra processamento."""
    response = await ai_fallback.generate_fallback_response(
        user_message="quero falar com um atendente humano",
    )
    assert "[HANDOFF]" in response.text


@pytest.mark.asyncio
async def test_fallback_unknown_message_uses_generic_template():
    # String sem nenhuma palavra-chave (e sem 'oi', 'nao', etc dentro de outra palavra)
    response = await ai_fallback.generate_fallback_response(
        user_message="xyzqwerty asdfgh zxcvb mnopq",
    )
    assert response.text
    assert response.provider_used == "offline_fallback"
    # Generico inclui orientacao pra humano
    assert "[HANDOFF]" in response.text or "atendente" in response.text.lower()


@pytest.mark.asyncio
async def test_fallback_empty_message_returns_generic():
    response = await ai_fallback.generate_fallback_response(user_message="")
    assert response.text
    assert response.provider_used == "offline_fallback"


# ══════════════════════════════════════════════════════════════════════════════
# Sync version
# ══════════════════════════════════════════════════════════════════════════════


def test_sync_fallback_works_without_db():
    response = ai_fallback.generate_fallback_response_sync(
        user_message="quero meu boleto",
        contact_name="Ana",
    )
    assert response.text
    assert "Ana" in response.text or "boleto" in response.text.lower()


def test_sync_fallback_handles_unknown():
    response = ai_fallback.generate_fallback_response_sync(
        user_message="xyzabcdefnonsense",
    )
    assert response.text
    assert response.tokens_used == 0


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════


def test_detect_intent_returns_none_for_garbage():
    intent = ai_fallback._detect_intent("xyzqwerty12345nonsense")
    assert intent is None


def test_detect_intent_normalizes_case_and_accents():
    assert ai_fallback._detect_intent("FALTAS") == "attendance_query"
    assert ai_fallback._detect_intent("Frequência") == "attendance_query"


def test_intent_templates_cover_all_keywords():
    """Toda key em INTENT_KEYWORDS deve ter template em INTENT_TEMPLATES."""
    for intent_key in ai_fallback.INTENT_KEYWORDS:
        assert intent_key in ai_fallback.INTENT_TEMPLATES, (
            f"Falta template para intent '{intent_key}'"
        )
