import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Boleto
from app.models.schedule import ClassSchedule
from app.models.student import AttendanceRecord, Grade, Student
from app.utils.exceptions import NotFoundError


async def get_student_by_ra(
    db: AsyncSession, tenant_id: uuid.UUID, registration_number: str
) -> Optional[Student]:
    result = await db.execute(
        select(Student).where(
            Student.tenant_id == tenant_id,
            Student.registration_number == registration_number,
        )
    )
    return result.scalar_one_or_none()


async def get_student_by_id(
    db: AsyncSession, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> Student:
    result = await db.execute(
        select(Student).where(Student.tenant_id == tenant_id, Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Aluno")
    return student


async def list_students(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Student], int]:
    query = select(Student).where(Student.tenant_id == tenant_id)

    if search:
        query = query.where(
            Student.full_name.ilike(f"%{search}%")
            | Student.registration_number.ilike(f"%{search}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.offset((page - 1) * size).limit(size).order_by(Student.full_name)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_grades(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    academic_period: Optional[str] = None,
    subject: Optional[str] = None,
) -> list[Grade]:
    query = select(Grade).where(Grade.tenant_id == tenant_id, Grade.student_id == student_id)
    if academic_period:
        query = query.where(Grade.academic_period == academic_period)
    if subject:
        query = query.where(Grade.subject_name.ilike(f"%{subject}%"))

    result = await db.execute(query.order_by(Grade.academic_period.desc(), Grade.subject_name))
    return result.scalars().all()


async def get_attendance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    academic_period: Optional[str] = None,
) -> list[AttendanceRecord]:
    query = select(AttendanceRecord).where(
        AttendanceRecord.tenant_id == tenant_id,
        AttendanceRecord.student_id == student_id,
    )
    if academic_period:
        query = query.where(AttendanceRecord.academic_period == academic_period)

    result = await db.execute(query)
    return result.scalars().all()


async def get_schedule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    course: str,
    semester: int,
    academic_period: str,
) -> list[ClassSchedule]:
    result = await db.execute(
        select(ClassSchedule)
        .where(
            ClassSchedule.tenant_id == tenant_id,
            ClassSchedule.course == course,
            ClassSchedule.semester == semester,
            ClassSchedule.academic_period == academic_period,
        )
        .order_by(ClassSchedule.day_of_week, ClassSchedule.start_time)
    )
    return result.scalars().all()


async def get_boletos(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    status: Optional[str] = None,
) -> list[Boleto]:
    query = select(Boleto).where(Boleto.tenant_id == tenant_id, Boleto.student_id == student_id)
    if status:
        query = query.where(Boleto.status == status)

    result = await db.execute(query.order_by(Boleto.reference_month.desc()))
    return result.scalars().all()
