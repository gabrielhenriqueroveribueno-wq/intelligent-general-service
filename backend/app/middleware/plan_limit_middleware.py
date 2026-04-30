"""
Plan limits middleware — bloqueia features quando tenant ultrapassa limites do plano.

Planos:
  - trial:      300 msgs/mês, 3 usuários, sem slides, sem integrações externas
  - starter:    2.000 msgs/mês, 10 usuários, slides OK
  - pro:        10.000 msgs/mês, 50 usuários, tudo OK
  - enterprise: sem limite

O contador de mensagens é atualizado pelo message_tasks.py via Redis
(key: plan:msgs:{tenant_id}:{YYYY-MM}).
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

PLAN_LIMITS: dict[str, dict] = {
    "trial": {
        "messages_per_month": 300,
        "max_users": 3,
        "blocked_prefixes": ["/api/v1/slides", "/api/v1/integrations", "/api/v1/webhooks"],
    },
    "starter": {
        "messages_per_month": 2_000,
        "max_users": 10,
        "blocked_prefixes": ["/api/v1/integrations"],
    },
    "pro": {
        "messages_per_month": 10_000,
        "max_users": 50,
        "blocked_prefixes": [],
    },
    "enterprise": {
        "messages_per_month": 0,  # 0 = sem limite
        "max_users": 0,
        "blocked_prefixes": [],
    },
    # "basic" é legado — equivalente a starter
    "basic": {
        "messages_per_month": 2_000,
        "max_users": 10,
        "blocked_prefixes": [],
    },
}


class PlanLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = "redis://localhost:6379/3"):
        super().__init__(app)
        self._redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Só aplica em rotas autenticadas da API
        if not path.startswith("/api/v1/") or path.startswith("/api/v1/health"):
            return await call_next(request)

        tenant_id, plan = _extract_tenant_plan(request)
        if not tenant_id or not plan:
            return await call_next(request)

        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])

        # Verifica prefixos bloqueados para este plano
        for blocked in limits["blocked_prefixes"]:
            if path.startswith(blocked):
                return JSONResponse(
                    status_code=402,
                    content={
                        "detail": f"Funcionalidade não disponível no plano {plan}. Faça upgrade para acessar.",
                        "code": "PLAN_LIMIT_FEATURE",
                        "upgrade_required": True,
                    },
                )

        # Verifica limite de mensagens mensais
        msg_limit = limits["messages_per_month"]
        if msg_limit > 0 and path.startswith("/api/v1/webhook/whatsapp"):
            try:
                from datetime import datetime
                month_key = f"plan:msgs:{tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
                redis = await self._get_redis()
                count = int(await redis.get(month_key) or 0)
                if count >= msg_limit:
                    return JSONResponse(
                        status_code=402,
                        content={
                            "detail": f"Limite de {msg_limit} mensagens/mês atingido para o plano {plan}.",
                            "code": "PLAN_LIMIT_MESSAGES",
                            "upgrade_required": True,
                        },
                    )
            except Exception as exc:
                logger.debug("Plan limit Redis error (passthrough): %s", exc)

        return await call_next(request)


def _extract_tenant_plan(request: Request) -> tuple[str | None, str | None]:
    """Extrai tenant_id e plan do JWT sem validar assinatura."""
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None, None
        token = auth[7:]
        import base64
        import json
        parts = token.split(".")
        if len(parts) != 3:
            return None, None
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("tenant_id"), payload.get("plan", "basic")
    except Exception:
        return None, None
