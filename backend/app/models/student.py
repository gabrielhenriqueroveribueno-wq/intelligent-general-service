# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantMixin, TimestampMixin


class Student(Base, TenantMixin, TimestampMixin):
    """Dados do aluno."""

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_number", name="uq_student_tenant_ra"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False)  # RA
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[Optional[str]] = mapped_column(String(255))  # encrypted
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    course: Mapped[Optional[str]] = mapped_column(String(255))
    semester: Mapped[Optional[int]] = mapped_column()
    enrollment_status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # active, locked, graduated, dropped
    enrollment_date: Mapped[Optional[object]] = mapped_column(Date)
    # Risco de evasão (calculado por Celery periodicamente)
    evasion_risk_score: Mapped[int] = mapped_column(Integer, default=0)
    evasion_risk_level: Mapped[str] = mapped_column(String(20), default="low", index=True)
    evasion_risk_updated_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))
    evasion_factors: Mapped[Optional[str]] = mapped_column(Text)  # JSON serializado

    # Relationships
    tenant: Mapped[object] = relationship("Tenant", back_populates="students", lazy="noload")
    grades: Mapped[list] = relationship("Grade", back_populates="student", lazy="noload")
    attendance_records: Mapped[list] = relationship(
        "AttendanceRecord", back_populates="student", lazy="noload"
    )
    boletos: Mapped[list] = relationship("Boleto", back_populates="student", lazy="noload")


class Grade(Base, TenantMixin, TimestampMixin):
    """Notas do aluno."""

    __tablename__ = "grades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_code: Mapped[Optional[str]] = mapped_column(String(50))
    academic_period: Mapped[str] = mapped_column(String(20), nullable=False)  # "2026.1"
    grade_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    grade_type: Mapped[str] = mapped_column(String(50), default="P1")  # P1, P2, final, recovery
    status: Mapped[Optional[str]] = mapped_column(String(20))  # approved, failed, pending

    student: Mapped[object] = relationship("Student", back_populates="grades", lazy="noload")


class AttendanceRecord(Base, TenantMixin, TimestampMixin):
    """Registro de frequÃªncia do aluno."""

    __tablename__ = "attendance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    subject_code: Mapped[Optional[str]] = mapped_column(String(50))
    subject_name: Mapped[Optional[str]] = mapped_column(String(255))
    academic_period: Mapped[str] = mapped_column(String(20), nullable=False)
    total_classes: Mapped[int] = mapped_column(default=0)
    attended: Mapped[int] = mapped_column(default=0)
    absence_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    student: Mapped[object] = relationship(
        "Student", back_populates="attendance_records", lazy="noload"
    )
