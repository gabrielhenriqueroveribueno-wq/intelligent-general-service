# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Modelo de subscricao de relatorios por email.

Cada tenant pode ter varias subscricoes com configuracoes independentes:
- emails dos destinatarios (nao precisa ser user do sistema)
- periodo (daily/weekly/monthly)
- ativa/inativa
- horario de envio (HH:MM formato 24h)

Isso permite que a escola mande relatorio pro diretor que nao usa o painel.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ReportSubscription(Base, TenantMixin, TimestampMixin):
    """Configuracao de envio automatico de relatorios executivos."""

    __tablename__ = "report_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    period: Mapped[str] = mapped_column(
        String(20), nullable=False, default="weekly"
    )  # daily, weekly, monthly
    recipients: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )  # lista de emails
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    send_hour_utc: Mapped[int] = mapped_column(default=11)  # 8h BRT = 11h UTC
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
