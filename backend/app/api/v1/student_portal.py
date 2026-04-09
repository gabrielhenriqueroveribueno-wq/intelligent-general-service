"""
Portal Web do Aluno — micro-frontend API.

Autenticação independente via RA + senha (JWT customizado).
Endpoints GET-only para o aluno consultar seus dados.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import AsyncSessionLocal, _set_tenant_context
from app.models.billing import Boleto
from app.models.schedule import ClassSchedule
from app.models.student import AttendanceRecord, Grade, Student
from app.utils.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)

router = APIRouter()
security = HTTPBearer()


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════


class StudentLoginRequest(BaseModel):
    registration_number: str  # RA
    password: str
    tenant_id: str


class StudentLoginResponse(BaseModel):
    access_token: str
    student_name: str
    course: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# Auth dependency
# ══════════════════════════════════════════════════════════════════════════════


async def get_student_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Valida JWT e retorna payload do aluno."""
    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("portal") != "student":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return payload


async def get_portal_db(
    student_data: dict = Depends(get_student_from_token),
) -> AsyncSession:
    """Yield session with tenant context for portal."""
    session = AsyncSessionLocal()
    tenant_id = student_data.get("tenant_id", "")
    if tenant_id:
        await _set_tenant_context(session, tenant_id)
    return session


# ══════════════════════════════════════════════════════════════════════════════
# Login
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/login", response_model=StudentLoginResponse)
async def student_login(body: StudentLoginRequest):
    """
    Login do aluno via RA + senha.

    O aluno precisa ter uma senha definida no campo Student.cpf (reutilizado como hash).
    Em produção, adicionar campo `password_hash` dedicado ao Student model.
    """
    async with AsyncSessionLocal() as db:
        tenant_uuid = uuid.UUID(body.tenant_id)
        await _set_tenant_context(db, body.tenant_id)

        result = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_uuid,
                Student.registration_number == body.registration_number,
            )
        )
        student = result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="RA não encontrado",
            )

        # Use CPF field as password hash (temporary) or check plain CPF
        # In production: add Student.password_hash column
        student_password = student.cpf or ""
        if not student_password or not _check_student_password(body.password, student_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Senha incorreta",
            )

        token = create_access_token(
            {
                "sub": str(student.id),
                "tenant_id": str(student.tenant_id),
                "ra": student.registration_number,
                "portal": "student",
            }
        )

        return StudentLoginResponse(
            access_token=token,
            student_name=student.full_name,
            course=student.course,
        )


def _check_student_password(plain: str, stored: str) -> bool:
    """Check password — supports bcrypt hash or plain CPF match."""
    if stored.startswith("$2"):
        return verify_password(plain, stored)
    # Fallback: CPF match (last 6 digits as password)
    return plain == stored[-6:] if len(stored) >= 6 else plain == stored


# ══════════════════════════════════════════════════════════════════════════════
# Profile
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/me")
async def get_my_profile(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
):
    """Retorna perfil do aluno logado."""
    student_id = uuid.UUID(student_data["sub"])
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    return {
        "id": str(student.id),
        "registration_number": student.registration_number,
        "full_name": student.full_name,
        "email": student.email,
        "course": student.course,
        "semester": student.semester,
        "enrollment_status": student.enrollment_status,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Grades
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/grades")
async def get_my_grades(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
    period: Optional[str] = None,
):
    """Retorna notas do aluno logado."""
    student_id = uuid.UUID(student_data["sub"])
    tenant_id = uuid.UUID(student_data["tenant_id"])

    stmt = select(Grade).where(
        Grade.tenant_id == tenant_id,
        Grade.student_id == student_id,
    )
    if period:
        stmt = stmt.where(Grade.academic_period == period)

    stmt = stmt.order_by(Grade.subject_name, Grade.grade_type)
    result = await db.execute(stmt)
    grades = result.scalars().all()

    return {
        "items": [
            {
                "subject_name": g.subject_name,
                "subject_code": g.subject_code,
                "academic_period": g.academic_period,
                "grade_type": g.grade_type,
                "grade_value": float(g.grade_value) if g.grade_value else None,
                "status": g.status,
            }
            for g in grades
        ],
        "total": len(grades),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Attendance
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/attendance")
async def get_my_attendance(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
):
    """Retorna frequência do aluno logado."""
    student_id = uuid.UUID(student_data["sub"])
    tenant_id = uuid.UUID(student_data["tenant_id"])

    result = await db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.student_id == student_id,
        )
        .order_by(AttendanceRecord.subject_name)
    )
    records = result.scalars().all()

    return {
        "items": [
            {
                "subject_name": a.subject_name,
                "subject_code": a.subject_code,
                "academic_period": a.academic_period,
                "total_classes": a.total_classes,
                "attended": a.attended,
                "absence_pct": float(a.absence_pct) if a.absence_pct else 0,
            }
            for a in records
        ],
        "total": len(records),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Schedule
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/schedule")
async def get_my_schedule(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
):
    """Retorna grade horária do aluno logado."""
    student_id = uuid.UUID(student_data["sub"])
    tenant_id = uuid.UUID(student_data["tenant_id"])

    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    result = await db.execute(
        select(ClassSchedule)
        .where(
            ClassSchedule.tenant_id == tenant_id,
            ClassSchedule.course == student.course,
            ClassSchedule.semester == student.semester,
        )
        .order_by(ClassSchedule.day_of_week, ClassSchedule.start_time)
    )
    schedules = result.scalars().all()

    days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    return {
        "items": [
            {
                "day": days[s.day_of_week] if s.day_of_week < len(days) else str(s.day_of_week),
                "subject_name": s.subject_name,
                "subject_code": s.subject_code,
                "start_time": str(s.start_time)[:5] if s.start_time else "",
                "end_time": str(s.end_time)[:5] if s.end_time else "",
                "room": s.room,
                "professor": s.professor,
            }
            for s in schedules
        ],
        "total": len(schedules),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Boletos / Financial
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/boletos")
async def get_my_boletos(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
    status_filter: Optional[str] = None,
):
    """Retorna boletos do aluno logado."""
    student_id = uuid.UUID(student_data["sub"])
    tenant_id = uuid.UUID(student_data["tenant_id"])

    stmt = select(Boleto).where(
        Boleto.tenant_id == tenant_id,
        Boleto.student_id == student_id,
    )
    if status_filter:
        stmt = stmt.where(Boleto.status == status_filter)

    stmt = stmt.order_by(Boleto.due_date.desc())
    result = await db.execute(stmt)
    boletos = result.scalars().all()

    return {
        "items": [
            {
                "id": str(b.id),
                "reference_month": b.reference_month,
                "amount": float(b.amount),
                "due_date": str(b.due_date) if b.due_date else None,
                "status": b.status,
                "barcode": b.barcode,
                "pix_code": b.pix_code,
                "pdf_url": b.pdf_url,
                "installment_number": b.installment_number,
            }
            for b in boletos
        ],
        "total": len(boletos),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Library
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/library")
async def get_my_loans(
    student_data: dict = Depends(get_student_from_token),
    db: AsyncSession = Depends(get_portal_db),
):
    """Retorna empréstimos ativos na biblioteca."""
    student_id = uuid.UUID(student_data["sub"])
    tenant_id = uuid.UUID(student_data["tenant_id"])

    from app.services.library_service import get_library_summary

    summary = await get_library_summary(db, tenant_id, student_id)
    return summary
