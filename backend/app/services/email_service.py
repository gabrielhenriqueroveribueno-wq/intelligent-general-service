# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Servico de envio de email.
Usa Resend API quando RESEND_API_KEY estiver configurado.
Fallback para SMTP direto.
"""

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email_async(
    to: str,
    subject: str,
    body: str,
    attachment: bytes | None = None,
    attachment_name: str = "relatorio.pdf",
) -> bool:
    """Envia email via Resend API (async). Retorna True se enviado."""
    if not settings.RESEND_API_KEY or not settings.SMTP_FROM_EMAIL:
        logger.warning("Resend nao configurado, tentando SMTP")
        return send_email(to, subject, body, attachment, attachment_name)

    payload: dict = {
        "from": settings.SMTP_FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": body,
    }

    if attachment:
        import base64

        payload["attachments"] = [
            {
                "filename": attachment_name,
                "content": base64.b64encode(attachment).decode(),
            }
        ]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
            )

        if resp.status_code in (200, 201):
            logger.info("Email enviado via Resend para %s: %s", to, subject)
            return True

        logger.error("Resend erro %d: %s", resp.status_code, resp.text[:200])
        return False

    except Exception as exc:
        logger.error("Erro ao enviar via Resend: %s — tentando SMTP", exc)
        return send_email(to, subject, body, attachment, attachment_name)


def send_email(
    to: str,
    subject: str,
    body: str,
    attachment: bytes | None = None,
    attachment_name: str = "relatorio.pdf",
) -> bool:
    """Envia email via SMTP com anexo opcional. Retorna True se enviou."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("SMTP nao configurado, email nao enviado para %s", to)
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    if attachment:
        part = MIMEApplication(attachment, Name=attachment_name)
        part["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
        msg.attach(part)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())

        logger.info("Email enviado via SMTP para %s: %s", to, subject)
        return True

    except Exception as exc:
        logger.error("Erro ao enviar email para %s: %s", to, exc)
        return False
