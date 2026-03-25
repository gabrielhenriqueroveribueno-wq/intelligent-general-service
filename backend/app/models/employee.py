import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin


class Employee(Base, TenantMixin, TimestampMixin):
    """Dados do funcionário."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_number", name="uq_employee_tenant_num"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[Optional[str]] = mapped_column(String(255))  # encrypted
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    position: Mapped[Optional[str]] = mapped_column(String(255))
    hire_date: Mapped[Optional[object]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, on_leave, terminated

    tenant: Mapped[object] = relationship("Tenant", back_populates="employees", lazy="noload")
    payslips: Mapped[list] = relationship("Payslip", back_populates="employee", lazy="noload")
    vacation_balances: Mapped[list] = relationship(
        "VacationBalance", back_populates="employee", lazy="noload"
    )
    time_records: Mapped[list] = relationship(
        "TimeRecord", back_populates="employee", lazy="noload"
    )
    hr_requests: Mapped[list] = relationship(
        "HRRequest", back_populates="employee", lazy="noload"
    )


class Payslip(Base, TenantMixin, TimestampMixin):
    """Holerite do funcionário."""

    __tablename__ = "payslips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reference_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-03"
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deductions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)

    employee: Mapped[object] = relationship("Employee", back_populates="payslips", lazy="noload")


class VacationBalance(Base, TenantMixin, TimestampMixin):
    """Saldo de férias."""

    __tablename__ = "vacation_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    accrual_period_start: Mapped[Optional[object]] = mapped_column(Date)
    accrual_period_end: Mapped[Optional[object]] = mapped_column(Date)
    total_days: Mapped[int] = mapped_column(default=30)
    used_days: Mapped[int] = mapped_column(default=0)
    deadline_date: Mapped[Optional[object]] = mapped_column(Date)

    @property
    def remaining_days(self) -> int:
        return self.total_days - self.used_days

    employee: Mapped[object] = relationship(
        "Employee", back_populates="vacation_balances", lazy="noload"
    )


class TimeRecord(Base, TenantMixin, TimestampMixin):
    """Registro de ponto."""

    __tablename__ = "time_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    record_date: Mapped[Optional[object]] = mapped_column(Date)
    clock_in: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))
    clock_out: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))
    break_start: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))
    break_end: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))
    total_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(20), default="regular")  # regular, overtime, absence

    employee: Mapped[object] = relationship("Employee", back_populates="time_records", lazy="noload")


class HRRequest(Base, TenantMixin, TimestampMixin):
    """Solicitação de RH do funcionário."""

    __tablename__ = "hr_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # medical_cert, declaration, vacation
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    response_text: Mapped[Optional[str]] = mapped_column(Text)
    responded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    responded_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True))

    employee: Mapped[object] = relationship("Employee", back_populates="hr_requests", lazy="noload")
