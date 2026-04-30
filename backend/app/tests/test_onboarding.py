"""
Testes do servico de onboarding: criacao de tenant + admin + importacao CSV.

Estes testes sao CRITICOS pra seguranca: garantem que o vinculo tenant_id eh
respeitado em todas as operacoes (multi-tenancy nao pode vazar dados entre
escolas).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.student import Student
from app.models.tenant import Tenant, TenantSettings
from app.models.user import User
from app.services import onboarding_service

# ══════════════════════════════════════════════════════════════════════════════
# Slug normalization
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Faculdade Anchieta", "faculdade-anchieta"),
        ("  Colégio Novo Tempo  ", "col-gio-novo-tempo"),
        ("ABC123", "abc123"),
        ("foo--bar", "foo-bar"),
        ("--leading-trailing--", "leading-trailing"),
    ],
)
def test_normalize_slug(raw: str, expected: str):
    assert onboarding_service._normalize_slug(raw) == expected


# ══════════════════════════════════════════════════════════════════════════════
# Tenant + admin creation
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_tenant_with_admin_happy_path(db: AsyncSession):
    result = await onboarding_service.create_tenant_with_admin(
        db,
        tenant_name="Faculdade Teste",
        tenant_slug="teste-novo",
        plan="basic",
        admin_email="admin@teste.com",
        admin_password="SenhaForte@123",
        admin_full_name="Admin Teste",
    )
    await db.commit()

    assert result.slug == "teste-novo"
    assert result.admin_email == "admin@teste.com"

    # Verifica que tenant foi criado
    tenant = (await db.execute(select(Tenant).where(Tenant.id == result.tenant_id))).scalar_one()
    assert tenant.name == "Faculdade Teste"
    assert tenant.is_active is True

    # Verifica que settings foram criados
    settings = (
        await db.execute(select(TenantSettings).where(TenantSettings.tenant_id == result.tenant_id))
    ).scalar_one()
    assert settings.business_hours_start == "08:00"
    assert settings.business_hours_end == "18:00"

    # Verifica que admin user foi criado e vinculado ao tenant
    admin = (await db.execute(select(User).where(User.id == result.admin_user_id))).scalar_one()
    assert admin.tenant_id == tenant.id
    assert admin.role == "admin"
    assert admin.password_hash != "SenhaForte@123"  # nao armazena em texto plano


@pytest.mark.asyncio
async def test_create_tenant_rejects_duplicate_slug(db: AsyncSession, test_tenant: Tenant):
    with pytest.raises(ValueError, match="Slug.*ja esta em uso"):
        await onboarding_service.create_tenant_with_admin(
            db,
            tenant_name="Outra Faculdade",
            tenant_slug=test_tenant.slug,  # ja existe
            plan="basic",
            admin_email="outro@email.com",
            admin_password="SenhaForte@123",
            admin_full_name="Outro Admin",
        )


@pytest.mark.asyncio
async def test_create_tenant_rejects_duplicate_email(db: AsyncSession, test_admin_user: User):
    with pytest.raises(ValueError, match="Email.*ja esta em uso"):
        await onboarding_service.create_tenant_with_admin(
            db,
            tenant_name="Outra Faculdade",
            tenant_slug="outra-fac",
            plan="basic",
            admin_email=test_admin_user.email,
            admin_password="SenhaForte@123",
            admin_full_name="Outro Admin",
        )


@pytest.mark.asyncio
async def test_create_tenant_rejects_invalid_slug(db: AsyncSession):
    with pytest.raises(ValueError, match="Slug invalido"):
        await onboarding_service.create_tenant_with_admin(
            db,
            tenant_name="Foo",
            tenant_slug="ab",  # muito curto (min 3)
            plan="basic",
            admin_email="x@y.com",
            admin_password="SenhaForte@123",
            admin_full_name="X",
        )


# ══════════════════════════════════════════════════════════════════════════════
# CSV import — students
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_students_basic(db: AsyncSession, test_tenant: Tenant):
    csv_content = (
        b"registration_number,full_name,course,semester,enrollment_status,email,phone\n"
        b"20241001,Ana Silva,Computacao,4,active,ana@test.com,5511999991111\n"
        b"20241002,Bruno Costa,Engenharia,3,active,bruno@test.com,5511999992222\n"
    )

    result = await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    await db.commit()

    assert result.created == 2
    assert result.skipped == 0
    assert result.errors == []

    students = (
        (await db.execute(select(Student).where(Student.tenant_id == test_tenant.id)))
        .scalars()
        .all()
    )
    assert len(students) == 2
    assert {s.registration_number for s in students} == {"20241001", "20241002"}


@pytest.mark.asyncio
async def test_import_students_skips_duplicates(db: AsyncSession, test_tenant: Tenant):
    csv_content = b"registration_number,full_name\n20241001,Ana Silva\n"
    # Primeira importacao
    await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    await db.commit()

    # Segunda importacao com mesmo RA
    result = await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    assert result.created == 0
    assert result.skipped == 1


@pytest.mark.asyncio
async def test_import_students_validates_required_fields(db: AsyncSession, test_tenant: Tenant):
    csv_content = b"registration_number,full_name\n,Sem RA\n20241001,\n20241002,Valido\n"
    result = await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    assert result.created == 1
    assert len(result.errors) == 2


@pytest.mark.asyncio
async def test_import_students_handles_utf8_bom(db: AsyncSession, test_tenant: Tenant):
    """CSVs do Excel costumam ter BOM UTF-8 — temos que aceitar."""
    csv_content = b"\xef\xbb\xbfregistration_number,full_name\n20241001,Ana Silva\n"
    result = await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    assert result.created == 1


@pytest.mark.asyncio
async def test_import_students_rejects_oversized_file(db: AsyncSession, test_tenant: Tenant):
    # Header + 1 linha valida + max_rows pequeno
    csv_content = b"registration_number,full_name\n" + b"\n".join(
        f"2024{i:04d},Aluno {i}".encode() for i in range(20)
    )
    with pytest.raises(ValueError, match="excede o limite"):
        await onboarding_service.import_students_from_csv(
            db, test_tenant.id, csv_content, max_rows=10
        )


# ══════════════════════════════════════════════════════════════════════════════
# CSV import — employees
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_employees_basic(db: AsyncSession, test_tenant: Tenant):
    csv_content = (
        b"employee_number,full_name,department,position,status,email,phone,hire_date\n"
        b"FUNC001,Carlos Martins,Secretaria,Coordenador,active,carlos@test.com,55119991111,2019-03-15\n"
        b"FUNC002,Patricia Lima,Financeiro,Analista,active,patricia@test.com,55119992222,2021-08-01\n"
    )

    result = await onboarding_service.import_employees_from_csv(db, test_tenant.id, csv_content)
    await db.commit()

    assert result.created == 2
    assert result.skipped == 0

    employees = (
        (await db.execute(select(Employee).where(Employee.tenant_id == test_tenant.id)))
        .scalars()
        .all()
    )
    assert len(employees) == 2

    carlos = next(e for e in employees if e.employee_number == "FUNC001")
    assert carlos.hire_date is not None
    assert carlos.hire_date.isoformat() == "2019-03-15"


@pytest.mark.asyncio
async def test_import_employees_records_invalid_dates(db: AsyncSession, test_tenant: Tenant):
    csv_content = (
        b"employee_number,full_name,hire_date\n"
        b"FUNC001,Carlos Martins,15/03/2019\n"  # formato errado
    )
    result = await onboarding_service.import_employees_from_csv(db, test_tenant.id, csv_content)
    await db.commit()

    # Funcionario foi criado (data e opcional), mas erro foi registrado
    assert result.created == 1
    assert any("hire_date invalida" in e for e in result.errors)


# ══════════════════════════════════════════════════════════════════════════════
# CSV templates
# ══════════════════════════════════════════════════════════════════════════════


def test_students_template_includes_all_headers():
    csv = onboarding_service.generate_students_csv_template()
    first_line = csv.splitlines()[0]
    for header in onboarding_service.STUDENT_CSV_HEADERS:
        assert header in first_line


def test_employees_template_includes_all_headers():
    csv = onboarding_service.generate_employees_csv_template()
    first_line = csv.splitlines()[0]
    for header in onboarding_service.EMPLOYEE_CSV_HEADERS:
        assert header in first_line


def test_templates_have_example_rows():
    """Templates devem ter pelo menos 1 linha exemplo alem do header."""
    students_csv = onboarding_service.generate_students_csv_template()
    employees_csv = onboarding_service.generate_employees_csv_template()
    assert len(students_csv.splitlines()) >= 2
    assert len(employees_csv.splitlines()) >= 2


# ══════════════════════════════════════════════════════════════════════════════
# Tenant isolation (CRITICO — protecao multi-tenancy)
# ══════════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def second_tenant(db: AsyncSession) -> Tenant:
    tenant = Tenant(name="Outra Escola", slug="outra-escola", plan="basic")
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest.mark.asyncio
async def test_imported_students_are_isolated_per_tenant(
    db: AsyncSession, test_tenant: Tenant, second_tenant: Tenant
):
    """Importar mesma matricula em 2 tenants diferentes nao deve dar conflito."""
    csv_content = b"registration_number,full_name\n20241001,Ana Silva\n"

    r1 = await onboarding_service.import_students_from_csv(db, test_tenant.id, csv_content)
    await db.commit()
    r2 = await onboarding_service.import_students_from_csv(db, second_tenant.id, csv_content)
    await db.commit()

    assert r1.created == 1
    assert r2.created == 1  # mesmo RA, tenant diferente — deve criar

    # Cada tenant tem seu proprio aluno
    s1 = (
        (await db.execute(select(Student).where(Student.tenant_id == test_tenant.id)))
        .scalars()
        .all()
    )
    s2 = (
        (await db.execute(select(Student).where(Student.tenant_id == second_tenant.id)))
        .scalars()
        .all()
    )
    assert len(s1) == 1
    assert len(s2) == 1
    assert s1[0].id != s2[0].id
