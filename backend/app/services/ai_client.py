"""
Cliente unificado de IA — suporta Anthropic (Claude), Google (Gemini) e Groq (Llama).

Inclui Circuit Breaker com failover automático entre providers.
Se o provider principal falhar (timeout, 429, 500), tenta o próximo na cadeia.

Cadeia de fallback:
    groq → gemini → anthropic → erro final
    gemini → anthropic → groq → erro final
    anthropic → groq → gemini → erro final

Uso:
    result = await ai_complete(system_prompt, user_message, max_tokens=1024)
    print(result.text, result.tokens_used)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Circuit Breaker State
# ══════════════════════════════════════════════════════════════════════════════

CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT = 60  # seconds


@dataclass
class CircuitState:
    failures: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False


_circuit_states: dict[str, CircuitState] = {
    "groq": CircuitState(),
    "gemini": CircuitState(),
    "anthropic": CircuitState(),
}

FALLBACK_CHAINS: dict[str, list[str]] = {
    "groq": ["gemini", "anthropic"],
    "gemini": ["anthropic", "groq"],
    "anthropic": ["groq", "gemini"],
}


def _record_success(provider: str) -> None:
    state = _circuit_states[provider]
    state.failures = 0
    state.is_open = False


def _record_failure(provider: str) -> None:
    state = _circuit_states[provider]
    state.failures += 1
    state.last_failure_time = time.monotonic()
    if state.failures >= CIRCUIT_FAILURE_THRESHOLD:
        state.is_open = True
        logger.warning(
            "Circuit OPEN para provider '%s' após %d falhas consecutivas",
            provider,
            state.failures,
        )


def _is_available(provider: str) -> bool:
    state = _circuit_states[provider]
    if not state.is_open:
        return True
    elapsed = time.monotonic() - state.last_failure_time
    if elapsed >= CIRCUIT_RECOVERY_TIMEOUT:
        logger.info("Circuit HALF-OPEN para provider '%s' (tentando recovery)", provider)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Response dataclass
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class AIResponse:
    text: str
    tokens_used: int
    provider_used: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# Retryable exception detection
# ══════════════════════════════════════════════════════════════════════════════


def _is_retryable(exc: BaseException) -> bool:
    """Detecta erros que justificam retry: timeout, rate-limit (429), server error (5xx)."""
    exc_str = str(exc).lower()

    # Timeout
    if "timeout" in exc_str or "timed out" in exc_str:
        return True

    # Rate limit (429)
    if "429" in exc_str or "rate" in exc_str:
        return True

    # Server error (500, 502, 503)
    if any(code in exc_str for code in ("500", "502", "503", "internal server error")):
        return True

    # httpx / aiohttp connection errors
    if "connect" in exc_str and "error" in exc_str:
        return True

    # Anthropic-specific
    try:
        import anthropic

        if isinstance(exc, anthropic.RateLimitError):
            return True
        if isinstance(exc, anthropic.InternalServerError):
            return True
        if isinstance(exc, anthropic.APITimeoutError):
            return True
        if isinstance(exc, anthropic.APIConnectionError):
            return True
    except ImportError:
        pass

    # HTTP status code attribute (groq, httpx)
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status and isinstance(status, int):
        if status == 429 or status >= 500:
            return True

    return False


# ══════════════════════════════════════════════════════════════════════════════
# Provider implementations with tenacity retry
# ══════════════════════════════════════════════════════════════════════════════


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def _anthropic_complete(
    system: str,
    message: str,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> AIResponse:
    import anthropic

    effective_key = api_key or settings.ANTHROPIC_API_KEY
    client = anthropic.AsyncAnthropic(api_key=effective_key, timeout=30.0)

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": message}],
    )
    text = response.content[0].text.strip()
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return AIResponse(text=text, tokens_used=tokens, provider_used="anthropic")


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def _groq_complete(
    system: str,
    message: str,
    max_tokens: int,
) -> AIResponse:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=30.0)

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
    )
    text = response.choices[0].message.content.strip()
    tokens = 0
    if response.usage:
        tokens = (response.usage.prompt_tokens or 0) + (response.usage.completion_tokens or 0)
    return AIResponse(text=text, tokens_used=tokens, provider_used="groq")


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def _gemini_complete(
    system: str,
    message: str,
    max_tokens: int,
) -> AIResponse:
    import google.generativeai as genai

    genai.configure(api_key=settings.GOOGLE_API_KEY)

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
        ),
    )

    response = await model.generate_content_async(message)
    text = response.text.strip()

    tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = getattr(response.usage_metadata, "prompt_token_count", 0) + getattr(
            response.usage_metadata, "candidates_token_count", 0
        )

    return AIResponse(text=text, tokens_used=tokens, provider_used="gemini")


# ══════════════════════════════════════════════════════════════════════════════
# Provider dispatch map
# ══════════════════════════════════════════════════════════════════════════════

_PROVIDER_FN = {
    "groq": _groq_complete,
    "gemini": _gemini_complete,
    "anthropic": _anthropic_complete,
}


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point with Circuit Breaker + Failover
# ══════════════════════════════════════════════════════════════════════════════


async def ai_complete(
    system: str,
    message: str,
    max_tokens: int = 1024,
    api_key: Optional[str] = None,
) -> AIResponse:
    """
    Envia prompt para o provider configurado com Circuit Breaker e failover automático.

    Se o provider principal falhar (timeout, 429, 500), tenta automaticamente
    os providers de fallback na ordem definida em FALLBACK_CHAINS.
    """
    primary = settings.AI_PROVIDER.lower()
    providers_to_try = [primary] + FALLBACK_CHAINS.get(primary, [])

    last_error: Exception | None = None

    for provider in providers_to_try:
        if not _is_available(provider):
            logger.debug("Provider '%s' indisponível (circuit open), pulando", provider)
            continue

        fn = _PROVIDER_FN.get(provider)
        if not fn:
            continue

        try:
            kwargs: dict = {"system": system, "message": message, "max_tokens": max_tokens}
            if provider == "anthropic" and api_key:
                kwargs["api_key"] = api_key

            result = await fn(**kwargs)
            _record_success(provider)

            if provider != primary:
                logger.warning(
                    "Fallback ativado: resposta gerada por '%s' (primário '%s' indisponível)",
                    provider,
                    primary,
                )

            return result

        except (Exception, RetryError) as exc:
            _record_failure(provider)
            last_error = exc
            logger.error(
                "Provider '%s' falhou após retries: %s — tentando fallback",
                provider,
                str(exc)[:200],
            )
            continue

    # Todos os providers falharam
    error_msg = f"Todos os providers de IA falharam. Último erro: {last_error}"
    logger.critical(error_msg)
    raise RuntimeError(error_msg) from last_error
