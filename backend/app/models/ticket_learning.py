# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class TicketResolution(Base, TenantMixin, TimestampMixin):
    """Resolução indexada de ticket para aprendizado da IA."""

    __tablename__ = "ticket_resolutions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    problem_category: Mapped[str] = mapped_column(String(100), nullable=False)
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_steps: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    resolution_type: Mapped[str] = mapped_column(
        String(20), default="auto"
    )  # auto, human, escalated
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    resolution_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    ai_embedding_summary: Mapped[Optional[str]] = mapped_column(Text)
    times_used_as_reference: Mapped[int] = mapped_column(Integer, default=0)
