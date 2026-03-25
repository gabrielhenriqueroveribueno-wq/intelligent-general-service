import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin


class Boleto(Base, TenantMixin, TimestampMixin):
    """Boleto/cobrança do aluno."""

    __tablename__ = "boletos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reference_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-03"
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[Optional[object]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, paid, overdue
    barcode: Mapped[Optional[str]] = mapped_column(String(100))
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    second_copy_url: Mapped[Optional[str]] = mapped_column(Text)

    student: Mapped[object] = relationship("Student", back_populates="boletos", lazy="noload")
