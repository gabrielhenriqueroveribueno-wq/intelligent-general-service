import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin


class Contact(Base, TenantMixin, TimestampMixin):
    """Usuário final do WhatsApp (aluno ou funcionário)."""

    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone_number", name="uq_contact_tenant_phone"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_type: Mapped[str] = mapped_column(
        String(20), default="unknown"
    )  # student, employee, unknown
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)

    conversations: Mapped[list] = relationship(
        "Conversation", back_populates="contact", lazy="noload"
    )


class Conversation(Base, TenantMixin, TimestampMixin):
    """Conversa no WhatsApp."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, waiting_agent, closed
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    context_type: Mapped[Optional[str]] = mapped_column(String(20))  # student, employee, general
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)

    contact: Mapped[object] = relationship("Contact", back_populates="conversations", lazy="noload")
    messages: Mapped[list] = relationship(
        "Message", back_populates="conversation", lazy="noload"
    )


class Message(Base, TenantMixin, TimestampMixin):
    """Mensagem individual em uma conversa."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # user, bot, agent
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="text")  # text, image, document
    whatsapp_msg_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    ai_tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    intent: Mapped[Optional[str]] = mapped_column(String(50))
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    # Campos para mensagens com mídia
    whatsapp_media_id: Mapped[Optional[str]] = mapped_column(String(255))
    media_url: Mapped[Optional[str]] = mapped_column(String(500))
    media_mime_type: Mapped[Optional[str]] = mapped_column(String(100))

    conversation: Mapped[object] = relationship(
        "Conversation", back_populates="messages", lazy="noload"
    )
