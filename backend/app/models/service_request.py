# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ServiceRequest(Base, TenantMixin, TimestampMixin):
    """Solicitacao de servico executada via WhatsApp (boleto, matricula, documento, etc.)."""

    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, rejected
    request_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    result_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    processed_by: Mapped[str] = mapped_column(String(20), default="ai")  # ai, human
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
