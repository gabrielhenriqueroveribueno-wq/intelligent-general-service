"""
Servico de envio de email via SMTP.
Usado para relatorios semanais e notificacoes administrativas.
"""

import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to: str,
    subject: str,
    body: str,
    attachment: bytes | None = None,
    attachment_name: str = "relatorio.pdf",
) -> bool:
    """
    Envia email via SMTP com anexo opcional.
    Retorna True se enviou com sucesso.
    """
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("SMTP nao configurado, email nao enviado")
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

        logger.info("Email enviado para %s: %s", to, subject)
        return True

    except Exception as exc:
        logger.error("Erro ao enviar email para %s: %s", to, exc)
        return False
