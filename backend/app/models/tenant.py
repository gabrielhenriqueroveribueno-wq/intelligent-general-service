import uuid
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Representa uma instituição cliente no SaaS."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    whatsapp_phone: Mapped[Optional[str]] = mapped_column(String(20))
    whatsapp_token: Mapped[Optional[str]] = mapped_column(Text)  # encrypted
    whatsapp_phone_number_id: Mapped[Optional[str]] = mapped_column(String(50))
    claude_api_key: Mapped[Optional[str]] = mapped_column(Text)  # encrypted
    plan: Mapped[str] = mapped_column(String(50), default="basic")
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users: Mapped[list] = relationship("User", back_populates="tenant", lazy="noload")
    students: Mapped[list] = relationship("Student", back_populates="tenant", lazy="noload")
    employees: Mapped[list] = relationship("Employee", back_populates="tenant", lazy="noload")


class TenantSettings(Base, TimestampMixin):
    """Configurações detalhadas do tenant."""

    __tablename__ = "tenant_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    bot_name: Mapped[str] = mapped_column(String(100), default="Assistente IGS")
    welcome_message: Mapped[Optional[str]] = mapped_column(Text)
    business_hours_start: Mapped[Optional[str]] = mapped_column(String(5))  # "08:00"
    business_hours_end: Mapped[Optional[str]] = mapped_column(String(5))  # "18:00"
    business_days: Mapped[Optional[str]] = mapped_column(String(20), default="1,2,3,4,5")
    out_of_hours_message: Mapped[Optional[str]] = mapped_column(Text)
    max_auto_responses: Mapped[int] = mapped_column(default=10)
    language: Mapped[str] = mapped_column(String(5), default="pt-BR")
