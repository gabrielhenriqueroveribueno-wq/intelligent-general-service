"""
Endpoints administrativos de saude dos providers de IA.

Expoe:
- GET  /api/v1/admin/ai-health       → estado atual (cacheado, rapido)
- POST /api/v1/admin/ai-health/check → forca re-check ao vivo
- GET  /api/v1/admin/ai-health/circuit → estado dos circuit breakers
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends

from app.dependencies import require_roles
from app.services import ai_client, provider_health

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Cache em memoria (evita rajada de probes)
# ══════════════════════════════════════════════════════════════════════════════


_CACHE_TTL_SECONDS = 60.0
_cached_summary: Optional[dict] = None
_cached_at: float = 0.0


def _cache_fresh() -> bool:
    return _cached_summary is not None and (time.time() - _cached_at) < _CACHE_TTL_SECONDS


async def _refresh_cache() -> dict:
    global _cached_summary, _cached_at
    statuses = await provider_health.check_all_providers()
    _cached_summary = provider_health.summarize(statuses)
    _cached_at = time.time()
    return _cached_summary


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/ai-health")
async def get_ai_health(
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Retorna saude atual dos providers. Usa cache de 60s."""
    if _cache_fresh():
        assert _cached_summary is not None
        return {**_cached_summary, "cached": True}
    return {**await _refresh_cache(), "cached": False}


@router.post("/ai-health/check")
async def force_check_ai_health(
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Forca re-check ao vivo (bypass do cache)."""
    return {**await _refresh_cache(), "cached": False}


@router.get("/ai-health/circuit")
async def get_circuit_status(
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Estado atual dos circuit breakers (nao faz chamadas externas)."""
    circuits = {}
    for name, state in ai_client._circuit_states.items():
        circuits[name] = {
            "is_open": state.is_open,
            "failures": state.failures,
            "last_failure_time": state.last_failure_time,
            "seconds_since_failure": (
                int(time.monotonic() - state.last_failure_time)
                if state.last_failure_time > 0
                else None
            ),
        }
    return {
        "fallback_chains": ai_client.FALLBACK_CHAINS,
        "threshold": ai_client.CIRCUIT_FAILURE_THRESHOLD,
        "recovery_timeout_seconds": ai_client.CIRCUIT_RECOVERY_TIMEOUT,
        "circuits": circuits,
    }


@router.post("/ai-health/circuit/reset")
async def reset_circuits(
    _=Depends(require_roles("super_admin")),
) -> dict:
    """Zera todos os circuit breakers. Util apos resolver incidente."""
    for state in ai_client._circuit_states.values():
        state.failures = 0
        state.is_open = False
        state.last_failure_time = 0.0
    logger.warning("Circuit breakers resetados manualmente via admin endpoint")
    return {"success": True, "message": "Todos os circuit breakers foram resetados"}
