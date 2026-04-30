"""
Cálculo de risco de evasão por aluno.

Score 0-100 baseado em fatores ponderados:
  - Status de matrícula bloqueada/trancada
  - Médias de notas abaixo do mínimo
  - Taxa de frequência
  - Boletos em atraso
  - Sentimento negativo recente nas conversas
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass
class EvasionRisk:
    student_id: uuid.UUID
    score: int  # 0-100
    level: RiskLevel
    factors: list[str]  # legível para humanos


def _level_from_score(score: int) -> RiskLevel:
    if score >= 76:
        return "critical"
    if score >= 51:
        return "high"
    if score >= 26:
        return "medium"
    return "low"


async def compute_student_risk(db: AsyncSession, student_id: uuid.UUID) -> EvasionRisk:
    from decimal import Decimal

    from app.models.billing import Boleto
    from app.models.conversation import Contact, Conversation, Message
    from app.models.student import AttendanceRecord, Grade, Student

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return EvasionRisk(student_id=student_id, score=0, level="low", factors=[])

    score = 0
    factors: list[str] = []

    # ── Status de matrícula ──────────────────────────────────────────────────
    if student.enrollment_status == "dropped":
        return EvasionRisk(student_id=student_id, score=100, level="critical", factors=["Matrícula cancelada"])
    if student.enrollment_status == "locked":
        score += 40
        factors.append("Matrícula trancada")

    # ── Média de notas ───────────────────────────────────────────────────────
    grades_res = await db.execute(
        select(func.avg(Grade.grade_value)).where(
            Grade.student_id == student_id, Grade.grade_value.is_not(None)
        )
    )
    avg_grade: Decimal | None = grades_res.scalar()
    if avg_grade is not None:
        avg_f = float(avg_grade)
        if avg_f < 5.0:
            score += 30
            factors.append(f"Média de notas crítica ({avg_f:.1f})")
        elif avg_f < 7.0:
            score += 15
            factors.append(f"Média de notas abaixo do ideal ({avg_f:.1f})")

    # ── Frequência ───────────────────────────────────────────────────────────
    att_res = await db.execute(
        select(func.avg(AttendanceRecord.absence_pct)).where(
            AttendanceRecord.student_id == student_id
        )
    )
    avg_absence: float | None = att_res.scalar()
    if avg_absence is not None:
        if avg_absence >= 25.0:
            score += 25
            factors.append(f"Frequência crítica (falta {avg_absence:.0f}%)")
        elif avg_absence >= 15.0:
            score += 10
            factors.append(f"Frequência abaixo do ideal (falta {avg_absence:.0f}%)")

    # ── Boletos em atraso ────────────────────────────────────────────────────
    boletos_res = await db.execute(
        select(func.count()).where(
            Boleto.student_id == student_id, Boleto.status == "overdue"
        )
    )
    overdue_count: int = boletos_res.scalar() or 0
    if overdue_count >= 2:
        score += 20
        factors.append(f"{overdue_count} boleto(s) em atraso")
    elif overdue_count == 1:
        score += 10
        factors.append("1 boleto em atraso")

    # ── Sentimento negativo recente ──────────────────────────────────────────
    contact_res = await db.execute(
        select(Contact).where(Contact.student_id == student_id)
    )
    contact = contact_res.scalar_one_or_none()
    if contact:
        neg_count_res = await db.execute(
            select(func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.contact_id == contact.id,
                Message.sender_type == "user",
                Message.sentiment == "negative",
            )
        )
        neg_count: int = neg_count_res.scalar() or 0
        if neg_count >= 3:
            score += 15
            factors.append(f"{neg_count} mensagens com sentimento negativo")
        elif neg_count >= 1:
            score += 5
            factors.append("Sentimento negativo recente")

    score = min(100, score)
    return EvasionRisk(
        student_id=student_id,
        score=score,
        level=_level_from_score(score),
        factors=factors,
    )


async def compute_all_risks(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[EvasionRisk]:
    from app.models.student import Student

    students_res = await db.execute(
        select(Student.id).where(
            Student.tenant_id == tenant_id,
            Student.enrollment_status.in_(["active", "locked"]),
        )
    )
    student_ids = students_res.scalars().all()
    risks: list[EvasionRisk] = []
    for sid in student_ids:
        risk = await compute_student_risk(db, sid)
        risks.append(risk)
    return sorted(risks, key=lambda r: r.score, reverse=True)
