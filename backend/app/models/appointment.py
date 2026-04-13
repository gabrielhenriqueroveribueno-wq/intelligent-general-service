"""Modelo de agendamento de atendimento presencial."""

import uuid
from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class Appointment(Base, TenantMixin, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )

    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)

    department: Mapped[str] = mapped_column(String(100), nullable=False, default="secretaria")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(
            "scheduled", "confirmed", "cancelled", "completed", "no_show", name="appointment_status"
        ),
        default="scheduled",
        nullable=False,
    )
    protocol: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
