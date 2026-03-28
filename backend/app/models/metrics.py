import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class ResponseTimeMetric(Base, TenantMixin):
    """Metrica de tempo de resposta por mensagem."""

    __tablename__ = "response_time_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False
    )
    responder_type: Mapped[str] = mapped_column(String(20), nullable=False)  # bot, human, agent
    response_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    message_count_in_conversation: Mapped[Optional[int]] = mapped_column(Integer)
    was_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_time_total_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )


class WhatsAppMonitoredAccount(Base, TenantMixin, TimestampMixin):
    """Conta WhatsApp monitorada para comparacao IA vs Humano."""

    __tablename__ = "whatsapp_monitored_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(20), default="mixed"
    )  # human_agent, ai_bot, mixed
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    monitoring_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
