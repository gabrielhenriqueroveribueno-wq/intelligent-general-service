import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.schemas.student import (
    AttendanceResponse,
    BoletoResponse,
    ClassScheduleResponse,
    GradeResponse,
    StudentListResponse,
    StudentResponse,
)
from app.services import student_service

router = APIRouter()


@router.get("", response_model=StudentListResponse)
async def list_students(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    students, total = await student_service.list_students(db, tenant_id, search, page, size)
    return StudentListResponse(
        items=[StudentResponse.model_validate(s) for s in students],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    student = await student_service.get_student_by_id(db, tenant_id, student_id)
    return StudentResponse.model_validate(student)


@router.get("/{student_id}/grades", response_model=list[GradeResponse])
async def get_student_grades(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    period: Optional[str] = Query(default=None),
    subject: Optional[str] = Query(default=None),
):
    grades = await student_service.get_grades(db, tenant_id, student_id, period, subject)
    return [GradeResponse.model_validate(g) for g in grades]


@router.get("/{student_id}/attendance", response_model=list[AttendanceResponse])
async def get_student_attendance(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    period: Optional[str] = Query(default=None),
):
    records = await student_service.get_attendance(db, tenant_id, student_id, period)
    return [AttendanceResponse.model_validate(r) for r in records]


@router.get("/schedules/{course}/{semester}", response_model=list[ClassScheduleResponse])
async def get_class_schedule(
    course: str,
    semester: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    period: str = Query(default="2026.1"),
):
    schedules = await student_service.get_schedule(db, tenant_id, course, semester, period)
    return [ClassScheduleResponse.model_validate(s) for s in schedules]


@router.get("/{student_id}/boletos", response_model=list[BoletoResponse])
async def get_student_boletos(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    status: Optional[str] = Query(default=None),
):
    boletos = await student_service.get_boletos(db, tenant_id, student_id, status)
    return [BoletoResponse.model_validate(b) for b in boletos]


@router.get("/{student_id}/boletos/{boleto_id}/pdf")
async def download_boleto_pdf(
    student_id: uuid.UUID,
    boleto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    """Gera e retorna PDF do boleto."""
    from app.models.billing import Boleto
    from app.services.boleto_pdf_service import generate_boleto_pdf

    student = await student_service.get_student_by_id(db, tenant_id, student_id)
    result = await db.execute(
        select(Boleto).where(
            Boleto.id == boleto_id,
            Boleto.student_id == student_id,
            Boleto.tenant_id == tenant_id,
        )
    )
    boleto = result.scalar_one_or_none()
    if not boleto:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Boleto nao encontrado")

    pdf_bytes = generate_boleto_pdf(
        student_name=student.full_name,
        registration_number=student.registration_number,
        course=student.course or "",
        reference_month=boleto.reference_month,
        amount=boleto.amount,
        due_date=boleto.due_date,
        barcode=boleto.barcode,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="boleto_{boleto.reference_month}.pdf"'
        },
    )
