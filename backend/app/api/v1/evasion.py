from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.student import Student

router = APIRouter(prefix="/evasion", tags=["Evasion"])


class EvasionStudentOut(BaseModel):
    id: str
    full_name: str
    registration_number: str
    course: Optional[str]
    enrollment_status: str
    evasion_risk_score: int
    evasion_risk_level: str
    evasion_factors: list[str]

    model_config = {"from_attributes": True}


class EvasionSummaryOut(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    total_at_risk: int
    students: list[EvasionStudentOut]


@router.get("/at-risk", response_model=EvasionSummaryOut)
async def get_at_risk_students(
    level: Optional[str] = Query(None, description="Filtrar por nível: low/medium/high/critical"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
) -> EvasionSummaryOut:
    import json

    query = select(Student).where(
        Student.tenant_id == tenant_id,
        Student.enrollment_status.in_(["active", "locked"]),
        Student.evasion_risk_score > 0,
    )
    if level:
        query = query.where(Student.evasion_risk_level == level)

    query = query.order_by(Student.evasion_risk_score.desc()).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()

    # Counts por nível (sem filtro de level)
    counts_res = await db.execute(
        select(Student.evasion_risk_level, Student.id).where(
            Student.tenant_id == tenant_id,
            Student.enrollment_status.in_(["active", "locked"]),
        )
    )
    all_levels = counts_res.all()
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for row in all_levels:
        lv = row[0] or "low"
        if lv in counts:
            counts[lv] += 1

    def _parse_factors(s: Student) -> list[str]:
        try:
            return json.loads(s.evasion_factors) if s.evasion_factors else []
        except Exception:
            return []

    return EvasionSummaryOut(
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        total_at_risk=counts["critical"] + counts["high"] + counts["medium"],
        students=[
            EvasionStudentOut(
                id=str(s.id),
                full_name=s.full_name,
                registration_number=s.registration_number,
                course=s.course,
                enrollment_status=s.enrollment_status,
                evasion_risk_score=s.evasion_risk_score or 0,
                evasion_risk_level=s.evasion_risk_level or "low",
                evasion_factors=_parse_factors(s),
            )
            for s in students
        ],
    )


@router.post("/recalculate", status_code=202)
async def trigger_recalculate(
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Dispara o recálculo assíncrono do risco de evasão para todos os tenants."""
    from app.tasks.evasion_tasks import compute_evasion_risks_task

    compute_evasion_risks_task.delay()
    return {"status": "queued"}
