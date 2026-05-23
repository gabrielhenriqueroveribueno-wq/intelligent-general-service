# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Tarefa Celery: anonimização automática LGPD — roda mensalmente.

Anonimiza:
- Alunos inativos (enrollment_status='dropped'/'graduated') há mais de RETENTION_YEARS anos
- Funcionários demitidos há mais de RETENTION_YEARS anos

Isso atende ao princípio de minimização de dados da LGPD (Art. 6°, III)
e ao direito à eliminação após prazo necessário.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

RETENTION_YEARS = 5  # anos de retenção após inatividade


@celery_app.task(name="app.tasks.anonymization_tasks.auto_anonymize_task")
def auto_anonymize_task() -> dict:
    """Roda mensalmente: anonimiza registros além do prazo de retenção LGPD."""
    import asyncio

    return asyncio.run(_run())


async def _run() -> dict:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings
    from app.models.employee import Employee
    from app.models.student import Student
    from app.models.tenant import Tenant
    from app.services.anonymization_service import anonymize_employee, anonymize_student

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * RETENTION_YEARS)
    total_students = 0
    total_employees = 0

    async with session_factory() as db:
        tenants = (await db.execute(select(Tenant).where(Tenant.is_active))).scalars().all()

        for tenant in tenants:
            # Alunos inativos além do prazo
            students = (
                (
                    await db.execute(
                        select(Student).where(
                            Student.tenant_id == tenant.id,
                            Student.enrollment_status.in_(["dropped", "graduated"]),
                            Student.updated_at < cutoff,
                        )
                    )
                )
                .scalars()
                .all()
            )

            for student in students:
                try:
                    await anonymize_student(
                        db,
                        tenant.id,
                        student.id,
                        reason=f"Anonimização automática LGPD após {RETENTION_YEARS} anos",
                    )
                    total_students += 1
                except Exception as exc:
                    logger.warning("Erro ao anonimizar aluno %s: %s", student.id, exc)

            # Funcionários demitidos além do prazo
            employees = (
                (
                    await db.execute(
                        select(Employee).where(
                            Employee.tenant_id == tenant.id,
                            Employee.status == "inactive",
                            Employee.updated_at < cutoff,
                        )
                    )
                )
                .scalars()
                .all()
            )

            for employee in employees:
                try:
                    await anonymize_employee(
                        db,
                        tenant.id,
                        employee.id,
                        reason=f"Anonimização automática LGPD após {RETENTION_YEARS} anos",
                    )
                    total_employees += 1
                except Exception as exc:
                    logger.warning("Erro ao anonimizar funcionário %s: %s", employee.id, exc)

        await db.commit()

    await engine.dispose()

    logger.info(
        "Auto-anonimização concluída: %d alunos, %d funcionários",
        total_students,
        total_employees,
    )
    return {"students_anonymized": total_students, "employees_anonymized": total_employees}
