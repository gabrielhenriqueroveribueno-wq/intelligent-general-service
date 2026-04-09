import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class Ticket(Base, TenantMixin, TimestampMixin):
    """Ticket de atendimento."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(20), default="open"
    )  # open, in_progress, resolved, closed
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    media_urls: Mapped[Optional[dict]] = mapped_column("media_urls", JSONB, default=list)

    comments: Mapped[list] = relationship("TicketComment", back_populates="ticket", lazy="noload")


class TicketComment(Base, TimestampMixin):
    """Comentário em um ticket."""

    __tablename__ = "ticket_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)

    ticket: Mapped[object] = relationship("Ticket", back_populates="comments", lazy="noload")
