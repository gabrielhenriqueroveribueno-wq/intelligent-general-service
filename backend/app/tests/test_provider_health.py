"""
Testes do servico de monitoramento de saude dos providers de IA.

Mockam as funcoes de provider para nao bater nos servicos reais.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services import ai_client, provider_health

# ══════════════════════════════════════════════════════════════════════════════
# Error classification
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "exc_msg,expected_state",
    [
        ("Your credit balance is too low to access the API", provider_health.NO_CREDITS),
        ("billing required", provider_health.NO_CREDITS),
        ("insufficient funds", provider_health.NO_CREDITS),
        ("Rate limit reached for model", provider_health.RATE_LIMITED),
        ("HTTP 429 Too Many Requests", provider_health.RATE_LIMITED),
        ("TPD limit exceeded", provider_health.RATE_LIMITED),
        ("quota exceeded", provider_health.RATE_LIMITED),
        ("401 Unauthorized", provider_health.AUTH_ERROR),
        ("invalid api key", provider_health.AUTH_ERROR),
        ("authentication failed", provider_health.AUTH_ERROR),
        ("Connection timeout", provider_health.UNREACHABLE),
        ("connection refused", provider_health.UNREACHABLE),
        ("request timed out", provider_health.UNREACHABLE),
        ("some weird unmapped exception", provider_health.UNKNOWN_ERROR),
    ],
)
def test_classify_error_states(exc_msg: str, expected_state: str):
    state, _detail = provider_health._classify(Exception(exc_msg))
    assert state == expected_state


# ══════════════════════════════════════════════════════════════════════════════
# Per-provider checks (mocked)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_anthropic_returns_not_configured_when_key_missing():
    with patch.object(ai_client, "settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        # Recarregamos o modulo provider_health pra pegar o settings mockado
        from importlib import reload

        reload(provider_health)
        with patch.object(provider_health, "settings") as mock_settings2:
            mock_settings2.ANTHROPIC_API_KEY = ""
            result = await provider_health._check_anthropic()
            assert result.state == provider_health.NOT_CONFIGURED


# ══════════════════════════════════════════════════════════════════════════════
# Summary aggregation
# ══════════════════════════════════════════════════════════════════════════════


def test_summarize_all_healthy():
    statuses = [
        provider_health.ProviderStatus(name="anthropic", state="healthy", latency_ms=200),
        provider_health.ProviderStatus(name="groq", state="healthy", latency_ms=100),
        provider_health.ProviderStatus(name="gemini", state="healthy", latency_ms=300),
    ]
    summary = provider_health.summarize(statuses)
    assert summary["overall"] == "healthy"
    assert summary["healthy_count"] == 3
    assert summary["total_providers"] == 3
    assert summary["has_critical"] is False
    assert summary["has_degraded"] is False


def test_summarize_all_failed_is_critical():
    statuses = [
        provider_health.ProviderStatus(name="anthropic", state=provider_health.NO_CREDITS),
        provider_health.ProviderStatus(name="groq", state=provider_health.RATE_LIMITED),
        provider_health.ProviderStatus(name="gemini", state=provider_health.AUTH_ERROR),
    ]
    summary = provider_health.summarize(statuses)
    assert summary["overall"] == "critical"
    assert summary["healthy_count"] == 0
    assert summary["has_critical"] is True


def test_summarize_partial_healthy_is_degraded():
    statuses = [
        provider_health.ProviderStatus(name="anthropic", state="healthy"),
        provider_health.ProviderStatus(name="groq", state=provider_health.RATE_LIMITED),
        provider_health.ProviderStatus(name="gemini", state=provider_health.NO_CREDITS),
    ]
    summary = provider_health.summarize(statuses)
    assert summary["overall"] == "degraded"
    assert summary["healthy_count"] == 1
    assert summary["has_critical"] is True
    assert summary["has_degraded"] is True


def test_provider_status_to_dict_serializable():
    status = provider_health.ProviderStatus(name="anthropic", state="healthy", latency_ms=250)
    data = status.to_dict()
    assert data["name"] == "anthropic"
    assert data["state"] == "healthy"
    assert data["latency_ms"] == 250
    assert "checked_at" in data


# ══════════════════════════════════════════════════════════════════════════════
# Circuit breaker integration
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_all_providers_includes_circuit_state():
    """check_all_providers deve preencher circuit_open/circuit_failures."""
    # Limpa estado antes
    for state in ai_client._circuit_states.values():
        state.failures = 0
        state.is_open = False
        state.last_failure_time = 0.0

    # Simula falhas no anthropic
    ai_client._circuit_states["anthropic"].failures = 5
    ai_client._circuit_states["anthropic"].is_open = True

    # Mock async — funcao real, nao lambda, pra retornar coroutine awaitable
    async def mock_anthropic():
        return provider_health.ProviderStatus(name="anthropic", state="healthy", latency_ms=100)

    async def mock_groq():
        return provider_health.ProviderStatus(name="groq", state="healthy", latency_ms=100)

    async def mock_gemini():
        return provider_health.ProviderStatus(name="gemini", state="healthy", latency_ms=100)

    with (
        patch.object(provider_health, "_check_anthropic", new=mock_anthropic),
        patch.object(provider_health, "_check_groq", new=mock_groq),
        patch.object(provider_health, "_check_gemini", new=mock_gemini),
    ):
        statuses = await provider_health.check_all_providers()

    anthropic = next(s for s in statuses if s.name == "anthropic")
    assert anthropic.circuit_open is True
    assert anthropic.circuit_failures == 5

    groq = next(s for s in statuses if s.name == "groq")
    assert groq.circuit_open is False
    assert groq.circuit_failures == 0
