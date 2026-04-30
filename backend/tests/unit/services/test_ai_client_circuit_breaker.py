"""
Testes unitários do circuit breaker do ai_client.

Testam: abertura do circuito após N falhas, recovery timeout,
_is_retryable(), e a lógica de fallback sem chamar APIs reais.
"""

import time

import pytest

from app.services.ai_client import (
    CIRCUIT_FAILURE_THRESHOLD,
    CIRCUIT_RECOVERY_TIMEOUT,
    CircuitState,
    _circuit_states,
    _is_available,
    _is_retryable,
    _record_failure,
    _record_success,
)


@pytest.fixture(autouse=True)
def reset_circuit_states():
    """Reseta o estado dos circuits antes de cada teste."""
    for state in _circuit_states.values():
        state.failures = 0
        state.last_failure_time = 0.0
        state.is_open = False
    yield
    for state in _circuit_states.values():
        state.failures = 0
        state.last_failure_time = 0.0
        state.is_open = False


class TestCircuitState:
    def test_initial_state_is_closed(self):
        state = CircuitState()
        assert state.is_open is False
        assert state.failures == 0

    def test_record_failure_increments_count(self):
        _record_failure("groq")
        assert _circuit_states["groq"].failures == 1

    def test_circuit_opens_after_threshold(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("groq")
        assert _circuit_states["groq"].is_open is True

    def test_circuit_stays_closed_below_threshold(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD - 1):
            _record_failure("groq")
        assert _circuit_states["groq"].is_open is False

    def test_success_resets_failures(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("anthropic")
        _record_success("anthropic")
        assert _circuit_states["anthropic"].failures == 0
        assert _circuit_states["anthropic"].is_open is False

    def test_success_clears_open_circuit(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("gemini")
        assert _circuit_states["gemini"].is_open is True
        _record_success("gemini")
        assert _circuit_states["gemini"].is_open is False


class TestIsAvailable:
    def test_closed_circuit_is_available(self):
        assert _is_available("groq") is True

    def test_open_circuit_is_not_available(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("anthropic")
        assert _is_available("anthropic") is False

    def test_half_open_after_recovery_timeout(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("gemini")
        # Simula que o timeout de recovery já passou
        _circuit_states["gemini"].last_failure_time = time.monotonic() - CIRCUIT_RECOVERY_TIMEOUT - 1
        assert _is_available("gemini") is True

    def test_still_blocked_before_recovery_timeout(self):
        for _ in range(CIRCUIT_FAILURE_THRESHOLD):
            _record_failure("groq")
        # Falha muito recente
        _circuit_states["groq"].last_failure_time = time.monotonic()
        assert _is_available("groq") is False


class TestIsRetryable:
    @pytest.mark.parametrize("error_msg", [
        "timeout",
        "timed out",
        "rate limit exceeded",
        "429 too many requests",
        "500 internal server error",
        "502 bad gateway",
        "503 service unavailable",
        "connection error",
    ])
    def test_retryable_error_messages(self, error_msg: str):
        exc = Exception(error_msg)
        assert _is_retryable(exc) is True

    def test_non_retryable_error(self):
        exc = ValueError("invalid input")
        assert _is_retryable(exc) is False

    def test_status_code_429_is_retryable(self):
        exc = Exception("error")
        exc.status_code = 429
        assert _is_retryable(exc) is True

    def test_status_code_500_is_retryable(self):
        exc = Exception("error")
        exc.status_code = 500
        assert _is_retryable(exc) is True

    def test_status_code_400_is_not_retryable(self):
        exc = Exception("bad request")
        exc.status_code = 400
        assert _is_retryable(exc) is False

    def test_status_code_401_is_not_retryable(self):
        exc = Exception("unauthorized")
        exc.status_code = 401
        assert _is_retryable(exc) is False
