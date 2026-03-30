"""
Models para o sistema de slides IA — professores geram e atualizam
apresentações seguindo o padrão institucional (ex.: Anchieta).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class SlideTemplate(Base, TenantMixin, TimestampMixin):
    """Padrão visual de slides da instituição (cores, fontes, layouts)."""

    __tablename__ = "slide_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_rules: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Regras de estilo: cores, fontes, layouts, estrutura de slides",
    )
    example_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Exemplo de conteúdo gerado para referência da IA",
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    presentations = relationship("SlidePresentation", back_populates="template")


class SlidePresentation(Base, TenantMixin, TimestampMixin):
    """Apresentação de slides gerada pela IA para um professor."""

    __tablename__ = "slide_presentations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slide_templates.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    slides_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array de slides: [{title, content, notes, layout}]",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", comment="draft | final"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_slides: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id])
    template = relationship("SlideTemplate", back_populates="presentations")
    generation_logs = relationship(
        "SlideGenerationLog",
        back_populates="presentation",
        order_by="SlideGenerationLog.created_at.desc()",
    )


class SlideGenerationLog(Base, TenantMixin):
    """Histórico de prompts e tokens usados na geração de slides."""

    __tablename__ = "slide_generation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    presentation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slide_presentations.id"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="create | update | regenerate"
    )
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="groq")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    presentation = relationship("SlidePresentation", back_populates="generation_logs")
    teacher = relationship("User", foreign_keys=[teacher_id])
