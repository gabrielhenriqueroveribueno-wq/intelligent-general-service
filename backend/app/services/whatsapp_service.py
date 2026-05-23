# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
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


async def send_template_message(
    phone_number_id: str,
    access_token: str,
    to: str,
    template_name: str,
    language_code: str = "pt_BR",
    components: list | None = None,
) -> Optional[str]:
    """
    Envia mensagem usando template aprovado na Meta.

    components exemplo (corpo com variáveis):
    [{"type": "body", "parameters": [{"type": "text", "text": "João"}, {"type": "text", "text": "R$ 350,00"}]}]
    """
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            msg_id = data.get("messages", [{}])[0].get("id")
            logger.info("Template '%s' enviado para %s: %s", template_name, to, msg_id)
            return msg_id
        except httpx.HTTPStatusError as e:
            logger.error("Erro ao enviar template %s: %s", template_name, e.response.text)
            return None
        except Exception as e:
            logger.error("Erro inesperado ao enviar template: %s", e)
            return None


async def send_document_message(
    phone_number_id: str,
    access_token: str,
    to: str,
    media_url: str,
    filename: str,
    caption: str = "",
) -> Optional[str]:
    """Envia documento (PDF, etc.) via WhatsApp Business Cloud API."""
    url = f"{settings.WHATSAPP_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {
            "link": media_url,
            "filename": filename,
        },
    }
    if caption:
        payload["document"]["caption"] = caption

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            msg_id = response.json().get("messages", [{}])[0].get("id")
            logger.info("Documento '%s' enviado para %s: %s", filename, to, msg_id)
            return msg_id
        except Exception as e:
            logger.error("Erro ao enviar documento: %s", e)
            return None


async def mark_message_read(phone_number_id: str, access_token: str, message_id: str) -> bool:
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
