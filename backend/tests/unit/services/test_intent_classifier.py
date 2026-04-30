"""
Testes unitários do intent_classifier — IA mockada, sem custo real.

Cobre: parse de JSON, fallback para 'unknown', intent inválido,
propagação de entities e contexto de usuário.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai_client import AIResponse
from app.services.intent_classifier import VALID_INTENTS, classify_intent


def _ai_response(intent: str, entities: dict | None = None) -> AIResponse:
    payload = {"intent": intent, "entities": entities or {}}
    return AIResponse(text=json.dumps(payload), tokens_used=10, provider_used="mock")


@pytest.fixture()
def mock_ai(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr("app.services.intent_classifier.ai_complete", mock)
    return mock


class TestClassifyIntent:
    async def test_grade_query_classified_correctly(self, mock_ai):
        mock_ai.return_value = _ai_response("grade_query", {"subject": "Cálculo"})
        result = await classify_intent("Qual minha nota de Cálculo?")
        assert result["intent"] == "grade_query"
        assert result["entities"]["subject"] == "Cálculo"

    async def test_unknown_intent_fallback(self, mock_ai):
        mock_ai.return_value = _ai_response("totally_invalid_intent")
        result = await classify_intent("algo aleatório")
        assert result["intent"] == "unknown"

    async def test_all_valid_intents_accepted(self, mock_ai):
        for intent in VALID_INTENTS:
            mock_ai.return_value = _ai_response(intent)
            result = await classify_intent("mensagem qualquer")
            assert result["intent"] == intent

    async def test_returns_unknown_on_ai_exception(self, mock_ai):
        mock_ai.side_effect = RuntimeError("AI unavailable")
        result = await classify_intent("mensagem")
        assert result["intent"] == "unknown"

    async def test_returns_unknown_on_malformed_json(self, mock_ai):
        mock_ai.return_value = AIResponse(text="não é json", tokens_used=5, provider_used="mock")
        result = await classify_intent("mensagem")
        assert result["intent"] == "unknown"

    async def test_extracts_json_from_wrapped_text(self, mock_ai):
        # IA às vezes retorna texto antes/depois do JSON
        mock_ai.return_value = AIResponse(
            text='A intenção é: {"intent": "boleto_query", "entities": {}} obrigado.',
            tokens_used=15,
            provider_used="mock",
        )
        result = await classify_intent("Quero ver meu boleto")
        assert result["intent"] == "boleto_query"

    async def test_student_context_passed_to_ai(self, mock_ai):
        mock_ai.return_value = _ai_response("grade_query")
        await classify_intent("minha nota", context_type="student")
        call_kwargs = mock_ai.call_args
        system_arg = call_kwargs[1]["system"] if call_kwargs[1] else call_kwargs[0][0]
        assert "aluno" in system_arg.lower()

    async def test_employee_context_passed_to_ai(self, mock_ai):
        mock_ai.return_value = _ai_response("payslip_query")
        await classify_intent("meu holerite", context_type="employee")
        call_kwargs = mock_ai.call_args
        system_arg = call_kwargs[1]["system"] if call_kwargs[1] else call_kwargs[0][0]
        assert "funcionário" in system_arg.lower()

    async def test_short_message_includes_bot_context(self, mock_ai):
        mock_ai.return_value = _ai_response("generate_pix")
        await classify_intent("sim", last_bot_message="Quer gerar o PIX para pagar?")
        call_kwargs = mock_ai.call_args
        message_arg = call_kwargs[1]["message"] if call_kwargs[1] else call_kwargs[0][1]
        assert "sim" in message_arg
        assert "Quer gerar" in message_arg

    async def test_long_message_not_wrapped_with_context(self, mock_ai):
        mock_ai.return_value = _ai_response("faq")
        long_msg = "A" * 50
        await classify_intent(long_msg, last_bot_message="contexto bot")
        call_kwargs = mock_ai.call_args
        message_arg = call_kwargs[1]["message"] if call_kwargs[1] else call_kwargs[0][1]
        assert "Última mensagem" not in message_arg

    async def test_entities_passed_through(self, mock_ai):
        entities = {"month": "março", "year": "2026"}
        mock_ai.return_value = _ai_response("boleto_query", entities)
        result = await classify_intent("boleto de março")
        assert result["entities"]["month"] == "março"
        assert result["entities"]["year"] == "2026"

    async def test_missing_entities_defaults_to_empty_dict(self, mock_ai):
        mock_ai.return_value = AIResponse(
            text='{"intent": "greeting"}', tokens_used=5, provider_used="mock"
        )
        result = await classify_intent("oi")
        assert result["entities"] == {}
