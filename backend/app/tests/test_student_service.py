import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.services.student_service import get_grades, get_student_by_ra, list_students


@pytest.mark.asyncio
async def test_get_student_by_ra_not_found(db: AsyncSession, test_tenant):
    student = await get_student_by_ra(db, test_tenant.id, "RA999999")
    assert student is None


@pytest.mark.asyncio
async def test_create_and_get_student(db: AsyncSession, test_tenant):
    student = Student(
        tenant_id=test_tenant.id,
        registration_number="12345",
        full_name="João da Silva",
        course="Engenharia de Software",
        semester=3,
        enrollment_status="active",
    )
    db.add(student)
    await db.commit()

    found = await get_student_by_ra(db, test_tenant.id, "12345")
    assert found is not None
    assert found.full_name == "João da Silva"


@pytest.mark.asyncio
async def test_list_students(db: AsyncSession, test_tenant):
    for i in range(3):
        student = Student(
            tenant_id=test_tenant.id,
            registration_number=f"9900{i}",
            full_name=f"Aluno Teste {i}",
            enrollment_status="active",
        )
        db.add(student)
    await db.commit()

    students, total = await list_students(db, test_tenant.id)
    assert total >= 3


@pytest.mark.asyncio
async def test_get_grades_empty(db: AsyncSession, test_tenant):
    grades = await get_grades(db, test_tenant.id, uuid.uuid4())
    assert grades == []
