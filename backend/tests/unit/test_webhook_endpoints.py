"""Testes unitários do webhook do WhatsApp."""

import hashlib
import hmac
import json
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


def make_signature(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


WHATSAPP_MESSAGE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "123456789",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "5511999999999",
                            "phone_number_id": "test_phone_id",
                        },
                        "contacts": [{"profile": {"name": "João"}, "wa_id": "5511888888888"}],
                        "messages": [
                            {
                                "from": "5511888888888",
                                "id": "wamid.test123",
                                "timestamp": "1700000000",
                                "text": {"body": "Olá, qual minha nota?"},
                                "type": "text",
                            }
                        ],
                    },
                    "field": "messages",
                }
            ],
        }
    ],
}


# ── GET — Verificação de token ─────────────────────────────────────────────────

class TestWebhookVerification:
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, client):
        with patch("app.api.v1.webhook.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "meu-token-secreto"
            resp = await client.get(
                "/api/v1/webhook/whatsapp",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "meu-token-secreto",
                    "hub.challenge": "challenge_abc_123",
                },
            )
        assert resp.status_code == 200
        assert "challenge_abc_123" in resp.text

    @pytest.mark.asyncio
    async def test_verify_wrong_token(self, client):
        with patch("app.api.v1.webhook.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "token-correto"
            resp = await client.get(
                "/api/v1/webhook/whatsapp",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "token-errado",
                    "hub.challenge": "xyz",
                },
            )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_verify_wrong_mode(self, client):
        with patch("app.api.v1.webhook.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "token"
            resp = await client.get(
                "/api/v1/webhook/whatsapp",
                params={
                    "hub.mode": "unsubscribe",
                    "hub.verify_token": "token",
                    "hub.challenge": "xyz",
                },
            )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_verify_numeric_challenge(self, client):
        """Challenge numérico deve ser retornado como inteiro."""
        with patch("app.api.v1.webhook.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "tk"
            resp = await client.get(
                "/api/v1/webhook/whatsapp",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "tk",
                    "hub.challenge": "98765",
                },
            )
        assert resp.status_code == 200
        assert resp.json() == 98765


# ── POST — Recebimento de mensagens ──────────────────────────────────────────

class TestWebhookPost:
    @pytest.mark.asyncio
    async def test_post_valid_message_enqueues_task(self, client):
        body = json.dumps(WHATSAPP_MESSAGE_PAYLOAD).encode()

        with patch("app.api.v1.webhook.settings") as mock_settings, \
             patch("app.api.v1.webhook.verify_webhook_signature", return_value=True), \
             patch("app.api.v1.webhook.process_incoming_message") as mock_task:
            mock_settings.WHATSAPP_APP_SECRET = "secret"
            mock_task.delay = MagicMock()

            resp = await client.post(
                "/api/v1/webhook/whatsapp",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "sha256=fakesig",
                },
            )

        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    @pytest.mark.asyncio
    async def test_post_invalid_signature_returns_401(self, client):
        body = json.dumps(WHATSAPP_MESSAGE_PAYLOAD).encode()

        with patch("app.api.v1.webhook.settings") as mock_settings, \
             patch("app.api.v1.webhook.verify_webhook_signature", return_value=False):
            mock_settings.WHATSAPP_APP_SECRET = "real-secret"

            resp = await client.post(
                "/api/v1/webhook/whatsapp",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "sha256=invalidsig",
                },
            )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_post_wrong_object_type_ignored(self, client):
        payload = {**WHATSAPP_MESSAGE_PAYLOAD, "object": "instagram"}
        body = json.dumps(payload).encode()

        with patch("app.api.v1.webhook.settings") as mock_settings, \
             patch("app.api.v1.webhook.verify_webhook_signature", return_value=True):
            mock_settings.WHATSAPP_APP_SECRET = "secret"

            resp = await client.post(
                "/api/v1/webhook/whatsapp",
                content=body,
                headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=x"},
            )

        assert resp.status_code == 200
        assert resp.json().get("status") == "ignored"

    @pytest.mark.asyncio
    async def test_post_no_secret_skips_signature_check(self, client):
        """Se WHATSAPP_APP_SECRET não está configurado, aceita sem validar assinatura."""
        body = json.dumps(WHATSAPP_MESSAGE_PAYLOAD).encode()

        with patch("app.api.v1.webhook.settings") as mock_settings, \
             patch("app.api.v1.webhook.process_incoming_message") as mock_task:
            mock_settings.WHATSAPP_APP_SECRET = ""
            mock_task.delay = MagicMock()

            resp = await client.post(
                "/api/v1/webhook/whatsapp",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
