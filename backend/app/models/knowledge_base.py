import uuid
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class KBCategory(Base, TenantMixin, TimestampMixin):
    """Categoria da base de conhecimento."""

    __tablename__ = "kb_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    articles: Mapped[list] = relationship("KBArticle", back_populates="category", lazy="noload")


class KBArticle(Base, TenantMixin, TimestampMixin):
    """Artigo da base de conhecimento (FAQ, respostas automáticas)."""

    __tablename__ = "kb_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    applies_to: Mapped[str] = mapped_column(String(20), default="all")  # student, employee, all
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    category: Mapped[Optional[object]] = relationship(
        "KBCategory", back_populates="articles", lazy="noload"
    )
