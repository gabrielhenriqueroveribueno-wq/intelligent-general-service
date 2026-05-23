# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Monitoramento de saúde dos providers de IA.

Faz uma chamada minimalista em cada provider (Anthropic, Groq, Gemini) e
categoriza o estado:

- healthy: respondeu ok
- rate_limited: 429 / quota / TPD
- no_credits: saldo esgotado / billing
- auth_error: chave inválida
- unreachable: timeout / conexão
- unknown_error: outros

Também expõe estado do Circuit Breaker atual (de ai_client.py) pra gente
ver tudo num lugar só.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

from app.config import settings
from app.services import ai_client

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# State classification
# ══════════════════════════════════════════════════════════════════════════════


HEALTHY = "healthy"
RATE_LIMITED = "rate_limited"
NO_CREDITS = "no_credits"
AUTH_ERROR = "auth_error"
UNREACHABLE = "unreachable"
UNKNOWN_ERROR = "unknown_error"
NOT_CONFIGURED = "not_configured"


@dataclass
class ProviderStatus:
    name: str
    state: str
    detail: str = ""
    latency_ms: Optional[int] = None
    circuit_open: bool = False
    circuit_failures: int = 0
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


def _classify(exc: BaseException) -> tuple[str, str]:
    msg = str(exc).lower()

    if "credit balance" in msg or "billing" in msg or "insufficient" in msg:
        return NO_CREDITS, "Saldo esgotado ou billing bloqueado"

    if "rate limit" in msg or "429" in msg or "tpd" in msg or "quota" in msg:
        return RATE_LIMITED, "Rate limit ou quota diaria atingida"

    if "401" in msg or "unauthorized" in msg or "invalid api key" in msg or "authentication" in msg:
        return AUTH_ERROR, "Chave de API invalida ou ausente"

    if "timeout" in msg or "timed out" in msg or "connection" in msg:
        return UNREACHABLE, "Timeout ou falha de conexao"

    return UNKNOWN_ERROR, str(exc)[:200]


# ══════════════════════════════════════════════════════════════════════════════
# Per-provider checks (minimal calls — 1-token ping)
# ══════════════════════════════════════════════════════════════════════════════


_PROBE_SYSTEM = "ping"
_PROBE_MESSAGE = "ping"
_PROBE_MAX_TOKENS = 4
_PROBE_TIMEOUT_SECONDS = 15.0


async def _check_anthropic() -> ProviderStatus:
    name = "anthropic"
    if not settings.ANTHROPIC_API_KEY:
        return ProviderStatus(name=name, state=NOT_CONFIGURED, detail="ANTHROPIC_API_KEY ausente")

    start = time.perf_counter()
    try:
        await asyncio.wait_for(
            ai_client._anthropic_complete(
                system=_PROBE_SYSTEM,
                message=_PROBE_MESSAGE,
                max_tokens=_PROBE_MAX_TOKENS,
            ),
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        state, detail = _classify(exc)
        return ProviderStatus(name=name, state=state, detail=detail)

    latency = int((time.perf_counter() - start) * 1000)
    return ProviderStatus(name=name, state=HEALTHY, latency_ms=latency)


async def _check_groq() -> ProviderStatus:
    name = "groq"
    if not settings.GROQ_API_KEY:
        return ProviderStatus(name=name, state=NOT_CONFIGURED, detail="GROQ_API_KEY ausente")

    start = time.perf_counter()
    try:
        await asyncio.wait_for(
            ai_client._groq_complete(
                system=_PROBE_SYSTEM,
                message=_PROBE_MESSAGE,
                max_tokens=_PROBE_MAX_TOKENS,
            ),
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        state, detail = _classify(exc)
        return ProviderStatus(name=name, state=state, detail=detail)

    latency = int((time.perf_counter() - start) * 1000)
    return ProviderStatus(name=name, state=HEALTHY, latency_ms=latency)


async def _check_gemini() -> ProviderStatus:
    name = "gemini"
    if not settings.GOOGLE_API_KEY:
        return ProviderStatus(name=name, state=NOT_CONFIGURED, detail="GOOGLE_API_KEY ausente")

    start = time.perf_counter()
    try:
        await asyncio.wait_for(
            ai_client._gemini_complete(
                system=_PROBE_SYSTEM,
                message=_PROBE_MESSAGE,
                max_tokens=_PROBE_MAX_TOKENS,
            ),
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        state, detail = _classify(exc)
        return ProviderStatus(name=name, state=state, detail=detail)

    latency = int((time.perf_counter() - start) * 1000)
    return ProviderStatus(name=name, state=HEALTHY, latency_ms=latency)


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════


async def check_all_providers() -> list[ProviderStatus]:
    """Checa todos os providers em paralelo e adiciona estado do circuit breaker."""
    results = await asyncio.gather(
        _check_anthropic(),
        _check_groq(),
        _check_gemini(),
        return_exceptions=False,
    )

    for status in results:
        circuit = ai_client._circuit_states.get(status.name)
        if circuit:
            status.circuit_open = circuit.is_open
            status.circuit_failures = circuit.failures

    return list(results)


def summarize(statuses: list[ProviderStatus]) -> dict:
    """Consolida num sumário de alto nível."""
    healthy_count = sum(1 for s in statuses if s.state == HEALTHY)
    total = len(statuses)

    critical = [s for s in statuses if s.state in (NO_CREDITS, AUTH_ERROR)]
    degraded = [s for s in statuses if s.state in (RATE_LIMITED, UNREACHABLE, UNKNOWN_ERROR)]

    if healthy_count == 0:
        overall = "critical"
    elif critical or degraded:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "overall": overall,
        "healthy_count": healthy_count,
        "total_providers": total,
        "providers": [s.to_dict() for s in statuses],
        "has_critical": len(critical) > 0,
        "has_degraded": len(degraded) > 0,
        "checked_at": time.time(),
    }
