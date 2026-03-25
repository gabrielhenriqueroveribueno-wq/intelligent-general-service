import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_text_message(
    phone_number_id: str,
    access_token: str,
    to: str,
    body: str,
) -> Optional[str]:
    """Envia mensagem de texto via WhatsApp Business Cloud API."""
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            msg_id = data.get("messages", [{}])[0].get("id")
            logger.info("Mensagem enviada para %s: %s", to, msg_id)
            return msg_id
        except httpx.HTTPStatusError as e:
            logger.error("Erro ao enviar mensagem WhatsApp: %s", e.response.text)
            return None
        except Exception as e:
            logger.error("Erro inesperado ao enviar mensagem: %s", e)
            return None


async def send_interactive_list(
    phone_number_id: str,
    access_token: str,
    to: str,
    header: str,
    body: str,
    sections: list,
) -> Optional[str]:
    """Envia mensagem interativa com lista de opções."""
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {"button": "Ver opções", "sections": sections},
        },
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json().get("messages", [{}])[0].get("id")
        except Exception as e:
            logger.error("Erro ao enviar lista interativa: %s", e)
            return None


async def mark_message_read(
    phone_number_id: str, access_token: str, message_id: str
) -> bool:
    """Marca mensagem como lida."""
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.status_code == 200
        except Exception:
            return False
