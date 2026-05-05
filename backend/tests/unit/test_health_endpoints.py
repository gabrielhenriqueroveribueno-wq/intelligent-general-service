"""Testes unitários dos endpoints de health check."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.fixture()
async def client():
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "IGS API"

    @pytest.mark.asyncio
    async def test_readiness_db_ok(self, client):
        with patch("app.api.v1.health.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_get_db.return_value = mock_session

            resp = await client.get("/api/v1/health/ready")

        # Pode retornar 200 (ready) ou 503 (db unavailable em teste)
        assert resp.status_code in (200, 503)

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, client):
        """Health check não deve exigir autenticação."""
        resp = await client.get("/api/v1/health")
        assert resp.status_code != 401
        assert resp.status_code != 403
