"""Testes unitários dos endpoints de autenticação."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client():
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        with patch("app.api.v1.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = ("access_token_xyz", "refresh_token_xyz")
            resp = await client.post("/api/v1/auth/login", json={
                "email": "admin@test.com",
                "password": "senha123",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access_token_xyz"
        assert data["refresh_token"] == "refresh_token_xyz"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        from app.utils.exceptions import UnauthorizedError
        with patch("app.api.v1.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = UnauthorizedError("Credenciais inválidas")
            resp = await client.post("/api/v1/auth/login", json={
                "email": "wrong@test.com",
                "password": "wrongpass",
            })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        resp = await client.post("/api/v1/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "not-an-email",
            "password": "pass123",
        })
        assert resp.status_code == 422


# ── Refresh ───────────────────────────────────────────────────────────────────

class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_success(self, client):
        with patch("app.api.v1.auth.refresh_tokens", new_callable=AsyncMock) as mock_ref:
            mock_ref.return_value = ("new_access", "new_refresh")
            resp = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": "valid_refresh_token",
            })
        assert resp.status_code == 200
        assert resp.json()["access_token"] == "new_access"

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self, client):
        from app.utils.exceptions import UnauthorizedError
        with patch("app.api.v1.auth.refresh_tokens", new_callable=AsyncMock) as mock_ref:
            mock_ref.side_effect = UnauthorizedError("Token expirado")
            resp = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": "expired_token",
            })
        assert resp.status_code == 401


# ── Me ────────────────────────────────────────────────────────────────────────

class TestMe:
    @pytest.mark.asyncio
    async def test_me_returns_user(self, client):
        import os
        os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        from app.main import app
        from app.dependencies import get_current_user

        fake_user = MagicMock()
        fake_user.id = uuid.uuid4()
        fake_user.email = "user@test.com"
        fake_user.full_name = "Test User"
        fake_user.role = "admin"
        fake_user.tenant_id = uuid.uuid4()

        app.dependency_overrides[get_current_user] = lambda: fake_user
        try:
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake_token"},
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@test.com"
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client):
        resp = await client.get("/api/v1/auth/me")
        # FastAPI retorna 401 ou 403 dependendo do middleware de rate limit
        assert resp.status_code in (401, 403)


# ── Signup ────────────────────────────────────────────────────────────────────

class TestSignup:
    VALID_BODY = {
        "institution_name": "Faculdade Teste",
        "slug": "fac-teste",
        "admin_name": "Admin Teste",
        "admin_email": "admin@fac-teste.edu.br",
        "admin_password": "Senha@2025",
        "phone": "11999999999",
    }

    @pytest.mark.asyncio
    async def test_signup_invalid_slug_uppercase(self, client):
        body = {**self.VALID_BODY, "slug": "FacTeste"}
        resp = await client.post("/api/v1/auth/signup", json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_slug_too_short(self, client):
        body = {**self.VALID_BODY, "slug": "ab"}
        resp = await client.post("/api/v1/auth/signup", json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_weak_password(self, client):
        body = {**self.VALID_BODY, "admin_password": "123"}
        resp = await client.post("/api/v1/auth/signup", json=body)
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self, client):
        body = {**self.VALID_BODY, "admin_email": "not-an-email"}
        resp = await client.post("/api/v1/auth/signup", json=body)
        assert resp.status_code == 422
