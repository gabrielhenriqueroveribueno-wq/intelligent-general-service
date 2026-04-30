"""
Cache service — Redis-backed TTL cache para KB articles e tenant settings.

TTLs:
  - KB search results: 5 min (artigos mudam pouco)
  - Tenant settings: 10 min
  - Dashboard stats: 2 min
"""

import hashlib
import json
import logging
import uuid
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_TTL_KB = 300  # 5 min
_TTL_SETTINGS = 600  # 10 min
_TTL_DASHBOARD = 120  # 2 min

_redis_client: Optional[aioredis.Redis] = None


def _client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        url = settings.REDIS_URL.replace("/0", "/4")  # DB 4 para cache
        _redis_client = aioredis.from_url(url, decode_responses=True)
    return _redis_client


async def get(key: str) -> Optional[Any]:
    try:
        raw = await _client().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.debug("Cache get error (%s): %s", key, exc)
        return None


async def set(key: str, value: Any, ttl: int = 300) -> None:
    try:
        await _client().setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("Cache set error (%s): %s", key, exc)


async def delete(key: str) -> None:
    try:
        await _client().delete(key)
    except Exception as exc:
        logger.debug("Cache delete error (%s): %s", key, exc)


async def delete_pattern(pattern: str) -> None:
    try:
        r = _client()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as exc:
        logger.debug("Cache delete_pattern error (%s): %s", pattern, exc)


# ── Helpers por domínio ───────────────────────────────────────────────────────


def kb_key(tenant_id: uuid.UUID, query: str, applies_to: Optional[str] = None) -> str:
    h = hashlib.md5(f"{query}:{applies_to}".encode()).hexdigest()[:12]
    return f"kb:{tenant_id}:{h}"


def settings_key(tenant_id: uuid.UUID) -> str:
    return f"settings:{tenant_id}"


def dashboard_key(tenant_id: uuid.UUID) -> str:
    return f"dashboard:{tenant_id}"


async def get_kb(
    tenant_id: uuid.UUID, query: str, applies_to: Optional[str] = None
) -> Optional[list]:
    return await get(kb_key(tenant_id, query, applies_to))


async def set_kb(
    tenant_id: uuid.UUID, query: str, applies_to: Optional[str], articles: list
) -> None:
    await set(kb_key(tenant_id, query, applies_to), articles, ttl=_TTL_KB)


async def invalidate_kb(tenant_id: uuid.UUID) -> None:
    await delete_pattern(f"kb:{tenant_id}:*")


async def get_settings(tenant_id: uuid.UUID) -> Optional[dict]:
    return await get(settings_key(tenant_id))


async def set_settings(tenant_id: uuid.UUID, data: dict) -> None:
    await set(settings_key(tenant_id), data, ttl=_TTL_SETTINGS)


async def invalidate_settings(tenant_id: uuid.UUID) -> None:
    await delete(settings_key(tenant_id))


async def get_dashboard(tenant_id: uuid.UUID) -> Optional[dict]:
    return await get(dashboard_key(tenant_id))


async def set_dashboard(tenant_id: uuid.UUID, data: dict) -> None:
    await set(dashboard_key(tenant_id), data, ttl=_TTL_DASHBOARD)


async def invalidate_dashboard(tenant_id: uuid.UUID) -> None:
    await delete(dashboard_key(tenant_id))
