"""
Testes unitários do evasion_service com DB mockado.

Verifica: cálculo de score, níveis de risco, fatores gerados,
casos edge (aluno inexistente, dropped, score máximo clampado).
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.evasion_service import EvasionRisk, _level_from_score, compute_student_risk


STUDENT_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")


def _make_student(enrollment_status: str = "active"):
    from app.models.student import Student

    s = MagicMock(spec=Student)
    s.id = STUDENT_ID
    s.enrollment_status = enrollment_status
    return s


def _make_db(
    student=None,
    avg_grade: float | None = None,
    avg_absence: float | None = None,
    overdue_boletos: int = 0,
    negative_messages: int = 0,
    contact=None,
) -> AsyncMock:
    db = AsyncMock()
    call_count = 0

    async def execute(query):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # SELECT Student
            result.scalar_one_or_none.return_value = student
        elif call_count == 1:
            # avg Grade
            result.scalar.return_value = Decimal(str(avg_grade)) if avg_grade is not None else None
        elif call_count == 2:
            # avg Absence
            result.scalar.return_value = avg_absence
        elif call_count == 3:
            # overdue boletos count
            result.scalar.return_value = overdue_boletos
        elif call_count == 4:
            # contact
            result.scalar_one_or_none.return_value = contact
        elif call_count == 5:
            # negative message count
            result.scalar.return_value = negative_messages
        call_count += 1
        return result

    db.execute = execute
    return db


class TestLevelFromScore:
    @pytest.mark.parametrize("score,expected", [
        (0, "low"),
        (25, "low"),
        (26, "medium"),
        (50, "medium"),
        (51, "high"),
        (75, "high"),
        (76, "critical"),
        (100, "critical"),
    ])
    def test_level_boundaries(self, score: int, expected: str):
        assert _level_from_score(score) == expected


class TestComputeStudentRisk:
    async def test_student_not_found_returns_zero_risk(self):
        db = _make_db(student=None)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score == 0
        assert risk.level == "low"
        assert risk.factors == []

    async def test_dropped_student_returns_critical(self):
        student = _make_student("dropped")
        db = _make_db(student=student)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score == 100
        assert risk.level == "critical"
        assert "Matrícula cancelada" in risk.factors

    async def test_locked_student_adds_40_points(self):
        student = _make_student("locked")
        db = _make_db(student=student, avg_grade=8.0)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 40
        assert "Matrícula trancada" in risk.factors

    async def test_critical_grade_adds_30_points(self):
        student = _make_student("active")
        db = _make_db(student=student, avg_grade=4.0)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 30
        assert any("crítica" in f for f in risk.factors)

    async def test_below_ideal_grade_adds_15_points(self):
        student = _make_student("active")
        db = _make_db(student=student, avg_grade=6.0)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 15
        assert any("abaixo do ideal" in f for f in risk.factors)

    async def test_good_grade_adds_no_points(self):
        student = _make_student("active")
        db = _make_db(student=student, avg_grade=8.5)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score == 0
        assert risk.level == "low"

    async def test_critical_absence_adds_25_points(self):
        student = _make_student("active")
        db = _make_db(student=student, avg_absence=30.0)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 25
        assert any("Frequência crítica" in f for f in risk.factors)

    async def test_two_overdue_boletos_adds_20_points(self):
        student = _make_student("active")
        db = _make_db(student=student, overdue_boletos=2)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 20

    async def test_one_overdue_boleto_adds_10_points(self):
        student = _make_student("active")
        db = _make_db(student=student, overdue_boletos=1)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 10

    async def test_score_capped_at_100(self):
        student = _make_student("locked")
        contact = MagicMock()
        db = _make_db(
            student=student,
            avg_grade=3.0,
            avg_absence=35.0,
            overdue_boletos=5,
            negative_messages=10,
            contact=contact,
        )
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score <= 100

    async def test_multiple_factors_accumulate(self):
        student = _make_student("active")
        db = _make_db(student=student, avg_grade=4.0, overdue_boletos=2)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert risk.score >= 50
        assert len(risk.factors) >= 2

    async def test_evasion_risk_dataclass_fields(self):
        student = _make_student("active")
        db = _make_db(student=student)
        risk = await compute_student_risk(db, STUDENT_ID)
        assert isinstance(risk, EvasionRisk)
        assert risk.student_id == STUDENT_ID
        assert isinstance(risk.score, int)
        assert risk.level in ("low", "medium", "high", "critical")
        assert isinstance(risk.factors, list)
