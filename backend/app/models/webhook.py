import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WebhookEndpoint(Base):
    """Endpoint externo cadastrado por um tenant para receber eventos."""

    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(256))  # HMAC-SHA256 signing key
    description: Mapped[str | None] = mapped_column(String(255))

    # Eventos inscritos separados por vírgula, ex: "conversation.closed,ticket.created"
    events: Mapped[str] = mapped_column(Text, nullable=False, default="*")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deliveries: Mapped[list["WebhookDelivery"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Registro de cada tentativa de entrega de um evento para um endpoint."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("webhook_endpoints.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    attempt: Mapped[int] = mapped_column(Integer, default=1)
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    success: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    endpoint: Mapped["WebhookEndpoint"] = relationship(back_populates="deliveries")
