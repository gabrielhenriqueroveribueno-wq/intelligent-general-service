"""
Testes de isolamento multi-tenant.

Verifica que:
- JWT extração de tenant_id e plan funciona corretamente
- Middleware de plan limit bloqueia features por plano
- Prefixos bloqueados por plano retornam 402
- Tenant sem token passa livremente pelas rotas de health
"""

import base64
import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.middleware.plan_limit_middleware import PLAN_LIMITS, _extract_tenant_plan


def _make_jwt_token(payload: dict) -> str:
    """Cria um JWT fake (sem assinatura real) para testes."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    body_bytes = json.dumps(payload).encode()
    body = base64.urlsafe_b64encode(body_bytes).rstrip(b"=").decode()
    return f"{header}.{body}.fakesignature"


def _make_request(path: str = "/api/v1/slides", bearer_token: str | None = None):
    """Mock de Request do FastAPI."""
    from unittest.mock import MagicMock
    request = MagicMock()
    request.url.path = path
    if bearer_token:
        request.headers.get = lambda key, default="": f"Bearer {bearer_token}" if key == "Authorization" else default
    else:
        request.headers.get = lambda key, default="": default
    return request


class TestExtractTenantPlan:
    def test_extracts_tenant_id_and_plan(self):
        tenant_id = str(uuid.uuid4())
        token = _make_jwt_token({"tenant_id": tenant_id, "plan": "pro"})
        request = _make_request(bearer_token=token)
        extracted_tenant, extracted_plan = _extract_tenant_plan(request)
        assert extracted_tenant == tenant_id
        assert extracted_plan == "pro"

    def test_defaults_plan_to_basic_when_missing(self):
        tenant_id = str(uuid.uuid4())
        token = _make_jwt_token({"tenant_id": tenant_id})
        request = _make_request(bearer_token=token)
        _, plan = _extract_tenant_plan(request)
        assert plan == "basic"

    def test_returns_none_when_no_bearer_header(self):
        request = _make_request(bearer_token=None)
        tenant_id, plan = _extract_tenant_plan(request)
        assert tenant_id is None
        assert plan is None

    def test_returns_none_for_malformed_token(self):
        request = _make_request()
        request.headers.get = lambda k, d="": "Bearer notavalidtoken" if k == "Authorization" else d
        tenant_id, plan = _extract_tenant_plan(request)
        assert tenant_id is None

    def test_returns_none_for_non_bearer_auth(self):
        request = _make_request()
        request.headers.get = lambda k, d="": "Basic dXNlcjpwYXNz" if k == "Authorization" else d
        tenant_id, plan = _extract_tenant_plan(request)
        assert tenant_id is None

    @pytest.mark.parametrize("plan", ["trial", "starter", "pro", "enterprise", "basic"])
    def test_all_plans_extracted_correctly(self, plan: str):
        token = _make_jwt_token({"tenant_id": "abc", "plan": plan})
        request = _make_request(bearer_token=token)
        _, extracted_plan = _extract_tenant_plan(request)
        assert extracted_plan == plan


class TestPlanLimitsConfig:
    def test_trial_has_lowest_message_limit(self):
        assert PLAN_LIMITS["trial"]["messages_per_month"] == 300

    def test_enterprise_has_no_message_limit(self):
        assert PLAN_LIMITS["enterprise"]["messages_per_month"] == 0

    def test_trial_blocks_slides(self):
        assert "/api/v1/slides" in PLAN_LIMITS["trial"]["blocked_prefixes"]

    def test_trial_blocks_integrations(self):
        assert "/api/v1/integrations" in PLAN_LIMITS["trial"]["blocked_prefixes"]

    def test_pro_has_no_blocked_prefixes(self):
        assert PLAN_LIMITS["pro"]["blocked_prefixes"] == []

    def test_enterprise_has_no_blocked_prefixes(self):
        assert PLAN_LIMITS["enterprise"]["blocked_prefixes"] == []

    def test_starter_blocks_integrations_but_not_slides(self):
        starter = PLAN_LIMITS["starter"]
        assert "/api/v1/integrations" in starter["blocked_prefixes"]
        assert "/api/v1/slides" not in starter["blocked_prefixes"]

    def test_pro_user_limit_is_50(self):
        assert PLAN_LIMITS["pro"]["max_users"] == 50

    def test_trial_user_limit_is_3(self):
        assert PLAN_LIMITS["trial"]["max_users"] == 3


class TestPlanLimitMiddlewareDispatch:
    async def test_health_route_bypasses_middleware(self):
        from app.middleware.plan_limit_middleware import PlanLimitMiddleware

        app_mock = AsyncMock()
        middleware = PlanLimitMiddleware(app_mock, redis_url="redis://localhost:6379/3")

        response_mock = MagicMock()
        call_next = AsyncMock(return_value=response_mock)

        request = _make_request(path="/api/v1/health")
        result = await middleware.dispatch(request, call_next)

        call_next.assert_called_once()
        assert result == response_mock

    async def test_non_api_route_bypasses_middleware(self):
        from app.middleware.plan_limit_middleware import PlanLimitMiddleware

        app_mock = AsyncMock()
        middleware = PlanLimitMiddleware(app_mock, redis_url="redis://localhost:6379/3")

        response_mock = MagicMock()
        call_next = AsyncMock(return_value=response_mock)

        request = _make_request(path="/login")
        result = await middleware.dispatch(request, call_next)

        call_next.assert_called_once()

    async def test_trial_slides_returns_402(self):
        from fastapi.responses import JSONResponse
        from app.middleware.plan_limit_middleware import PlanLimitMiddleware

        app_mock = AsyncMock()
        middleware = PlanLimitMiddleware(app_mock, redis_url="redis://localhost:6379/3")

        call_next = AsyncMock()
        token = _make_jwt_token({"tenant_id": "tenant-1", "plan": "trial"})
        request = _make_request(path="/api/v1/slides", bearer_token=token)

        result = await middleware.dispatch(request, call_next)

        assert isinstance(result, JSONResponse)
        assert result.status_code == 402
        call_next.assert_not_called()

    async def test_pro_slides_passes_through(self):
        from app.middleware.plan_limit_middleware import PlanLimitMiddleware

        app_mock = AsyncMock()
        middleware = PlanLimitMiddleware(app_mock, redis_url="redis://localhost:6379/3")

        response_mock = MagicMock()
        call_next = AsyncMock(return_value=response_mock)
        token = _make_jwt_token({"tenant_id": "tenant-1", "plan": "pro"})
        request = _make_request(path="/api/v1/slides", bearer_token=token)

        result = await middleware.dispatch(request, call_next)

        call_next.assert_called_once()
        assert result == response_mock
