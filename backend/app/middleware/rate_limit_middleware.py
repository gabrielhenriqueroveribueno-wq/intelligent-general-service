"""
Rate limiting middleware — sliding window counter per tenant/IP via Redis.

Limits:
  - Authenticated (tenant): 600 req/min por tenant
  - Unauthenticated: 60 req/min por IP
  - /auth/login: 10 req/min por IP (brute-force protection)
  - /webhook/whatsapp: 300 req/min (Meta pode enviar em burst)
"""

import logging
import time

import redis.asyncio as aioredis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Endpoints com limites especiais (prefixo após /api/v1/)
_STRICT_PATHS = {"/api/v1/auth/login": (10, 60)}  # 10 req em 60s
_WEBHOOK_PATHS = {"/api/v1/webhook/"}  # mais tolerante
_EXEMPT_PATHS = {"/api/v1/health", "/api/v1/health/", "/metrics", "/docs", "/redoc", "/openapi.json"}

_DEFAULT_LIMIT = 600  # req por janela
_DEFAULT_WINDOW = 60  # segundos
_UNAUTH_LIMIT = 60
_WEBHOOK_LIMIT = 300


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = "redis://localhost:6379/3"):
        super().__init__(app)
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Isenta paths internos
        if any(path.startswith(e) for e in _EXEMPT_PATHS):
            return await call_next(request)

        # Determina limite e janela
        if path in _STRICT_PATHS:
            limit, window = _STRICT_PATHS[path]
            key_base = f"rl:strict:{request.client.host if request.client else 'unknown'}"
        elif any(path.startswith(wp) for wp in _WEBHOOK_PATHS):
            limit, window = _WEBHOOK_LIMIT, 60
            key_base = f"rl:webhook:{request.client.host if request.client else 'unknown'}"
        else:
            # Extrai tenant do JWT sem validar assinatura (só lê payload)
            tenant_id = _extract_tenant_id(request)
            if tenant_id:
                limit, window = _DEFAULT_LIMIT, _DEFAULT_WINDOW
                key_base = f"rl:tenant:{tenant_id}"
            else:
                limit, window = _UNAUTH_LIMIT, _DEFAULT_WINDOW
                key_base = f"rl:ip:{request.client.host if request.client else 'unknown'}"

        try:
            redis = await self._get_redis()
            now = int(time.time())
            bucket = now // window
            key = f"{key_base}:{bucket}"

            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window * 2)

            if count > limit:
                retry_after = window - (now % window)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Muitas requisições. Tente novamente em instantes.", "code": "RATE_LIMIT_EXCEEDED"},
                    headers={"Retry-After": str(retry_after), "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0"},
                )

            response = await call_next(request)
            remaining = max(0, limit - count)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except Exception as exc:
            # Redis indisponível: não bloqueia a requisição
            logger.warning("Rate limit Redis error (passthrough): %s", exc)
            return await call_next(request)


def _extract_tenant_id(request: Request) -> str | None:
    """Lê tenant_id do JWT sem validar assinatura (só para keying do rate limit)."""
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:]
        import base64
        import json

        parts = token.split(".")
        if len(parts) != 3:
            return None
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("tenant_id")
    except Exception:
        return None
