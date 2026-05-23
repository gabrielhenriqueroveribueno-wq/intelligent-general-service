# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Modelos para templates de mensagem WhatsApp (HSM) e notificações agendadas.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class MessageTemplate(Base, TenantMixin, TimestampMixin):
    """
    Referência a um template aprovado na Meta Business API.
    O template em si é criado no Meta Business Manager; aqui armazenamos
    apenas os metadados necessários para enviá-lo.
    """

    __tablename__ = "message_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # ID do template no Meta (nome usado na API, ex: "boleto_lembrete")
    meta_template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="pt_BR")
    # Categoria: MARKETING, UTILITY, AUTHENTICATION
    category: Mapped[str] = mapped_column(String(50), default="UTILITY")
    # Descrição dos parâmetros esperados no template
    # Ex: {"header": ["nome"], "body": ["vencimento", "valor"]}
    parameters_schema: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ScheduledNotification(Base, TenantMixin, TimestampMixin):
    """Registro de envio de notificação proativa via template."""

    __tablename__ = "scheduled_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_templates.id"), nullable=False
    )
    # Filtro de contatos que receberão a notificação (JSONB)
    # Ex: {"overdue_boletos": true, "days_ahead": 3}
    contact_filter: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # pending, running, completed, failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
