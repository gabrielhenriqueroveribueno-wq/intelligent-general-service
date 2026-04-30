"""
Contrato base que todo integrador de sistema academico deve implementar.

Por que Protocol e nao ABC: queremos duck typing e permitir que
integracoes externas (plugins) implementem sem herdar.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SyncResult:
    """Resultado de uma sincronizacao."""

    success: bool
    records_synced: int = 0
    students_created: int = 0
    students_updated: int = 0
    employees_created: int = 0
    employees_updated: int = 0
    grades_synced: int = 0
    boletos_synced: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def merge(self, other: "SyncResult") -> "SyncResult":
        return SyncResult(
            success=self.success and other.success,
            records_synced=self.records_synced + other.records_synced,
            students_created=self.students_created + other.students_created,
            students_updated=self.students_updated + other.students_updated,
            employees_created=self.employees_created + other.employees_created,
            employees_updated=self.employees_updated + other.employees_updated,
            grades_synced=self.grades_synced + other.grades_synced,
            boletos_synced=self.boletos_synced + other.boletos_synced,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


@runtime_checkable
class AcademicSystemIntegrator(Protocol):
    """
    Interface para integradores de sistema academico.

    Implementacoes:
    - SophiaIntegrator   → API do Sophia (Prima Tecnologia)
    - TotvsIntegrator    → API do TOTVS RM Educacional
    - GenericRestIntegrator → REST configuravel (qualquer sistema com JSON)
    """

    provider_type: str

    async def test_connection(self) -> tuple[bool, str]:
        """Verifica se as credenciais funcionam. Retorna (ok, mensagem)."""
        ...

    async def sync_students(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        """Importa/atualiza alunos."""
        ...

    async def sync_employees(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        """Importa/atualiza funcionarios."""
        ...

    async def sync_grades(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        """Sincroniza notas (apenas se a integracao suportar)."""
        ...

    async def sync_boletos(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        """Sincroniza boletos pendentes (apenas se a integracao suportar)."""
        ...

    async def sync_all(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        """Roda todas as sincronizacoes em sequencia."""
        ...


# ══════════════════════════════════════════════════════════════════════════════
# Helpers compartilhados (upsert)
# ══════════════════════════════════════════════════════════════════════════════


async def upsert_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    registration_number: str,
    full_name: str,
    course: Optional[str] = None,
    semester: Optional[int] = None,
    enrollment_status: str = "active",
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> tuple[bool, Any]:
    """
    Insere ou atualiza aluno por (tenant_id, registration_number).
    Retorna (created, student).
    """
    from sqlalchemy import select

    from app.models.student import Student

    result = await db.execute(
        select(Student).where(
            Student.tenant_id == tenant_id,
            Student.registration_number == registration_number,
        )
    )
    student = result.scalar_one_or_none()

    if student:
        student.full_name = full_name
        if course:
            student.course = course
        if semester is not None:
            student.semester = semester
        student.enrollment_status = enrollment_status
        if email:
            student.email = email
        if phone:
            student.phone = phone
        return False, student

    student = Student(
        tenant_id=tenant_id,
        registration_number=registration_number,
        full_name=full_name,
        course=course,
        semester=semester,
        enrollment_status=enrollment_status,
        email=email,
        phone=phone,
    )
    db.add(student)
    return True, student


async def upsert_employee(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    employee_number: str,
    full_name: str,
    department: Optional[str] = None,
    position: Optional[str] = None,
    status: str = "active",
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> tuple[bool, Any]:
    from sqlalchemy import select

    from app.models.employee import Employee

    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.employee_number == employee_number,
        )
    )
    employee = result.scalar_one_or_none()

    if employee:
        employee.full_name = full_name
        if department:
            employee.department = department
        if position:
            employee.position = position
        employee.status = status
        if email:
            employee.email = email
        if phone:
            employee.phone = phone
        return False, employee

    employee = Employee(
        tenant_id=tenant_id,
        employee_number=employee_number,
        full_name=full_name,
        department=department,
        position=position,
        status=status,
        email=email,
        phone=phone,
    )
    db.add(employee)
    return True, employee
