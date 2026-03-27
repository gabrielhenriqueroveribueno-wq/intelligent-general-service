import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.schemas.student import (
    AttendanceResponse,
    BoletoResponse,
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
