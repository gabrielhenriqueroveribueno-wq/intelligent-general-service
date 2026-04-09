import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class Boleto(Base, TenantMixin, TimestampMixin):
    """Boleto/cobrança do aluno."""

    __tablename__ = "boletos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    reference_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-03"
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[Optional[object]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, paid, overdue
    barcode: Mapped[Optional[str]] = mapped_column(String(100))
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    second_copy_url: Mapped[Optional[str]] = mapped_column(Text)

    # PIX fields
    pix_code: Mapped[Optional[str]] = mapped_column(Text)  # BR Code (copia e cola)
    pix_txid: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    pix_expiration: Mapped[Optional[object]] = mapped_column(Date)

    # Installment fields
    installment_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("installment_plans.id"), index=True
    )
    installment_number: Mapped[Optional[int]] = mapped_column(Integer)

    student: Mapped[object] = relationship("Student", back_populates="boletos", lazy="noload")
    installment_plan: Mapped[Optional[object]] = relationship(
        "InstallmentPlan", back_populates="boletos", lazy="noload"
    )


class InstallmentPlan(Base, TenantMixin, TimestampMixin):
    """Plano de parcelamento de débitos."""

    __tablename__ = "installment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    original_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # with interest
    num_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0"))
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, completed, cancelled
    negotiation_reason: Mapped[Optional[str]] = mapped_column(Text)
    negotiated_by: Mapped[Optional[str]] = mapped_column(String(50))  # "ai" or user_id
    original_boleto_ids: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    boletos: Mapped[list] = relationship("Boleto", back_populates="installment_plan", lazy="noload")
    student: Mapped[object] = relationship("Student", lazy="noload")
