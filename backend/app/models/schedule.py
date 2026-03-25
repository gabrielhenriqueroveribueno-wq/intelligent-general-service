import uuid
from typing import Optional

from sqlalchemy import Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, TenantMixin


class ClassSchedule(Base, TenantMixin, TimestampMixin):
    """Grade horária das aulas."""

    __tablename__ = "class_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course: Mapped[str] = mapped_column(String(255), nullable=False)
    semester: Mapped[Optional[int]] = mapped_column(Integer)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_code: Mapped[Optional[str]] = mapped_column(String(50))
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Seg .. 6=Dom
    start_time: Mapped[Optional[object]] = mapped_column(Time)
    end_time: Mapped[Optional[object]] = mapped_column(Time)
    room: Mapped[Optional[str]] = mapped_column(String(50))
    professor: Mapped[Optional[str]] = mapped_column(String(255))
    academic_period: Mapped[str] = mapped_column(String(20), nullable=False)  # "2026.1"
