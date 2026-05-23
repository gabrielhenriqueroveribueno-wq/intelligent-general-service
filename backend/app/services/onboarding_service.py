# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Servico de onboarding de novos tenants.

Encapsula:
- Criacao atomica de tenant + settings + admin user
- Importacao em massa de alunos/funcionarios via CSV
- Geracao de templates CSV para download

Transacoes sao commitadas ao final para evitar estado parcial.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.student import Student
from app.models.tenant import Tenant, TenantSettings
from app.models.user import User
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Data transfer objects
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class OnboardingResult:
    tenant_id: uuid.UUID
    slug: str
    admin_email: str
    admin_user_id: uuid.UUID


@dataclass
class ImportResult:
    created: int
    skipped: int
    errors: list[str]


# ══════════════════════════════════════════════════════════════════════════════
# Tenant + admin onboarding
# ══════════════════════════════════════════════════════════════════════════════


SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


def _normalize_slug(raw: str) -> str:
    slug = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


async def create_tenant_with_admin(
    db: AsyncSession,
    *,
    tenant_name: str,
    tenant_slug: str,
    plan: str,
    admin_email: str,
    admin_password: str,
    admin_full_name: str,
    bot_name: Optional[str] = None,
    welcome_message: Optional[str] = None,
    business_hours_start: Optional[str] = None,
    business_hours_end: Optional[str] = None,
) -> OnboardingResult:
    """Cria tenant, settings iniciais e usuario admin. Flush, sem commit."""
    slug = _normalize_slug(tenant_slug)
    if not SLUG_PATTERN.match(slug):
        raise ValueError("Slug invalido. Use letras minusculas, numeros e hifens (3-64 chars).")

    existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing.scalar_one_or_none():
        raise ValueError(f"Slug '{slug}' ja esta em uso")

    existing_user = await db.execute(select(User).where(User.email == admin_email.lower()))
    if existing_user.scalar_one_or_none():
        raise ValueError(f"Email '{admin_email}' ja esta em uso")

    tenant = Tenant(
        name=tenant_name.strip(),
        slug=slug,
        plan=plan or "basic",
        is_active=True,
    )
    db.add(tenant)
    await db.flush()

    settings = TenantSettings(
        tenant_id=tenant.id,
        bot_name=bot_name or "Assistente IGS",
        welcome_message=welcome_message,
        business_hours_start=business_hours_start or "08:00",
        business_hours_end=business_hours_end or "18:00",
        out_of_hours_message="Nosso horario de atendimento e de 8h as 18h. Retorno em breve!",
    )
    db.add(settings)

    admin = User(
        tenant_id=tenant.id,
        email=admin_email.strip().lower(),
        password_hash=hash_password(admin_password),
        full_name=admin_full_name.strip(),
        role="admin",
        is_active=True,
    )
    db.add(admin)

    await db.flush()

    logger.info(
        "Tenant '%s' criado com admin '%s' (tenant_id=%s)",
        slug,
        admin.email,
        tenant.id,
    )

    return OnboardingResult(
        tenant_id=tenant.id,
        slug=slug,
        admin_email=admin.email,
        admin_user_id=admin.id,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CSV import
# ══════════════════════════════════════════════════════════════════════════════


STUDENT_CSV_HEADERS = (
    "registration_number",
    "full_name",
    "course",
    "semester",
    "enrollment_status",
    "email",
    "phone",
)

EMPLOYEE_CSV_HEADERS = (
    "employee_number",
    "full_name",
    "department",
    "position",
    "status",
    "email",
    "phone",
    "hire_date",
)


def _read_csv(content: bytes) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(row) for row in reader]
    return rows


async def import_students_from_csv(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    content: bytes,
    max_rows: int = 10000,
) -> ImportResult:
    rows = _read_csv(content)
    if len(rows) > max_rows:
        raise ValueError(f"Arquivo excede o limite de {max_rows} linhas")

    created = 0
    skipped = 0
    errors: list[str] = []

    for idx, row in enumerate(rows, start=2):  # linha 1 e o header
        ra = (row.get("registration_number") or "").strip()
        name = (row.get("full_name") or "").strip()

        if not ra:
            errors.append(f"Linha {idx}: registration_number vazio")
            continue
        if not name:
            errors.append(f"Linha {idx}: full_name vazio")
            continue

        existing = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_id,
                Student.registration_number == ra,
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        semester_val: Optional[int] = None
        semester_raw = (row.get("semester") or "").strip()
        if semester_raw:
            try:
                semester_val = int(semester_raw)
            except ValueError:
                errors.append(f"Linha {idx}: semester invalido '{semester_raw}'")

        student = Student(
            tenant_id=tenant_id,
            registration_number=ra,
            full_name=name,
            course=(row.get("course") or "").strip() or None,
            semester=semester_val,
            enrollment_status=(row.get("enrollment_status") or "active").strip(),
            email=(row.get("email") or "").strip() or None,
            phone=(row.get("phone") or "").strip() or None,
        )
        db.add(student)
        created += 1

    await db.flush()
    logger.info(
        "Import alunos: tenant=%s criados=%d ignorados=%d erros=%d",
        tenant_id,
        created,
        skipped,
        len(errors),
    )
    return ImportResult(created=created, skipped=skipped, errors=errors[:50])


async def import_employees_from_csv(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    content: bytes,
    max_rows: int = 10000,
) -> ImportResult:
    rows = _read_csv(content)
    if len(rows) > max_rows:
        raise ValueError(f"Arquivo excede o limite de {max_rows} linhas")

    created = 0
    skipped = 0
    errors: list[str] = []

    for idx, row in enumerate(rows, start=2):
        num = (row.get("employee_number") or "").strip()
        name = (row.get("full_name") or "").strip()

        if not num:
            errors.append(f"Linha {idx}: employee_number vazio")
            continue
        if not name:
            errors.append(f"Linha {idx}: full_name vazio")
            continue

        existing = await db.execute(
            select(Employee).where(
                Employee.tenant_id == tenant_id,
                Employee.employee_number == num,
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        hire_dt: Optional[date] = None
        hire_raw = (row.get("hire_date") or "").strip()
        if hire_raw:
            try:
                hire_dt = date.fromisoformat(hire_raw)
            except ValueError:
                errors.append(f"Linha {idx}: hire_date invalida '{hire_raw}' (use YYYY-MM-DD)")

        employee = Employee(
            tenant_id=tenant_id,
            employee_number=num,
            full_name=name,
            department=(row.get("department") or "").strip() or None,
            position=(row.get("position") or "").strip() or None,
            status=(row.get("status") or "active").strip(),
            email=(row.get("email") or "").strip() or None,
            phone=(row.get("phone") or "").strip() or None,
            hire_date=hire_dt,
        )
        db.add(employee)
        created += 1

    await db.flush()
    logger.info(
        "Import funcionarios: tenant=%s criados=%d ignorados=%d erros=%d",
        tenant_id,
        created,
        skipped,
        len(errors),
    )
    return ImportResult(created=created, skipped=skipped, errors=errors[:50])


# ══════════════════════════════════════════════════════════════════════════════
# CSV template generators
# ══════════════════════════════════════════════════════════════════════════════


def generate_students_csv_template() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(STUDENT_CSV_HEADERS)
    writer.writerow(
        [
            "20241001",
            "Ana Carolina Silva",
            "Ciencia da Computacao",
            "4",
            "active",
            "ana.silva@aluno.anchieta.edu.br",
            "5511999881234",
        ]
    )
    writer.writerow(
        [
            "20241002",
            "Pedro Henrique Santos",
            "Engenharia Civil",
            "3",
            "active",
            "pedro.santos@aluno.anchieta.edu.br",
            "5511998774321",
        ]
    )
    return buf.getvalue()


def generate_employees_csv_template() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(EMPLOYEE_CSV_HEADERS)
    writer.writerow(
        [
            "FUNC001",
            "Carlos Eduardo Martins",
            "Secretaria Academica",
            "Coordenador",
            "active",
            "carlos.martins@anchieta.edu.br",
            "5511998001234",
            "2019-03-15",
        ]
    )
    writer.writerow(
        [
            "FUNC002",
            "Patricia Souza Lima",
            "Financeiro",
            "Analista Financeiro",
            "active",
            "patricia.lima@anchieta.edu.br",
            "5511997442118",
            "2021-08-01",
        ]
    )
    return buf.getvalue()
