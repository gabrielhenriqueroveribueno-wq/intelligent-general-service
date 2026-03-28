import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_webhook_verify_valid(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_verify_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_ignored_object(client: AsyncClient, monkeypatch):
    """Payloads que não são whatsapp_business_account devem ser ignorados."""
    monkeypatch.setattr("app.config.settings.WHATSAPP_APP_SECRET", "")
    response = await client.post(
        "/api/v1/webhook/whatsapp",
        json={"object": "instagram", "entry": []},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
