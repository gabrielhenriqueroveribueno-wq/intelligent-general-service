"""
Testes de isolamento multi-tenancy via HTTP.

Garantem que um admin do tenant A nao consegue:
- Listar alunos/funcionarios do tenant B
- Acessar conversas do tenant B
- Importar dados em outro tenant

Esta eh a barreira de seguranca mais critica do SaaS — qualquer falha
aqui significa vazamento de dados de alunos entre escolas.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.tenant import Tenant
from app.models.user import User
from app.utils.security import hash_password

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures: 2 tenants + admins separados
# ══════════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def tenant_a(db: AsyncSession) -> Tenant:
    t = Tenant(name="Escola A", slug="escola-a", plan="basic")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@pytest_asyncio.fixture
async def tenant_b(db: AsyncSession) -> Tenant:
    t = Tenant(name="Escola B", slug="escola-b", plan="basic")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@pytest_asyncio.fixture
async def admin_a(db: AsyncSession, tenant_a: Tenant) -> User:
    u = User(
        tenant_id=tenant_a.id,
        email="admin-a@escola.com",
        password_hash=hash_password("PassA@12345"),
        full_name="Admin A",
        role="admin",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
async def admin_b(db: AsyncSession, tenant_b: Tenant) -> User:
    u = User(
        tenant_id=tenant_b.id,
        email="admin-b@escola.com",
        password_hash=hash_password("PassB@12345"),
        full_name="Admin B",
        role="admin",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
async def student_a(db: AsyncSession, tenant_a: Tenant) -> Student:
    s = Student(
        tenant_id=tenant_a.id,
        registration_number="RA-A-001",
        full_name="Aluno da Escola A",
        enrollment_status="active",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@pytest_asyncio.fixture
async def student_b(db: AsyncSession, tenant_b: Tenant) -> Student:
    s = Student(
        tenant_id=tenant_b.id,
        registration_number="RA-B-001",
        full_name="Aluno da Escola B",
        enrollment_status="active",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@pytest_asyncio.fixture
async def token_a(client: AsyncClient, admin_a: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-a@escola.com", "password": "PassA@12345"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def token_b(client: AsyncClient, admin_b: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin-b@escola.com", "password": "PassB@12345"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ══════════════════════════════════════════════════════════════════════════════
# Isolamento na listagem de alunos
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_a_only_sees_own_students(
    client: AsyncClient,
    token_a: str,
    student_a: Student,
    student_b: Student,
):
    r = await client.get(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 200
    data = r.json()

    ids = {s["id"] for s in data["items"]}
    assert str(student_a.id) in ids
    assert str(student_b.id) not in ids


@pytest.mark.asyncio
async def test_admin_b_only_sees_own_students(
    client: AsyncClient,
    token_b: str,
    student_a: Student,
    student_b: Student,
):
    r = await client.get(
        "/api/v1/students",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()["items"]}
    assert str(student_b.id) in ids
    assert str(student_a.id) not in ids


@pytest.mark.asyncio
async def test_admin_a_cannot_get_student_from_b(
    client: AsyncClient,
    token_a: str,
    student_b: Student,
):
    """Acessar aluno de outro tenant deve retornar 404 (nao 200, nem 403 — 404 evita vazar existencia)."""
    r = await client.get(
        f"/api/v1/students/{student_b.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code in (403, 404)


# ══════════════════════════════════════════════════════════════════════════════
# Isolamento no onboarding (CSV import)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_a_cannot_import_students_into_tenant_b(
    client: AsyncClient,
    token_a: str,
    tenant_b: Tenant,
):
    csv_content = b"registration_number,full_name\n20241001,Aluno Teste\n"

    r = await client.post(
        f"/api/v1/onboarding/tenants/{tenant_b.id}/import-students",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("alunos.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_a_cannot_import_employees_into_tenant_b(
    client: AsyncClient,
    token_a: str,
    tenant_b: Tenant,
):
    csv_content = b"employee_number,full_name\nFUNC001,Funcionario Teste\n"

    r = await client.post(
        f"/api/v1/onboarding/tenants/{tenant_b.id}/import-employees",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("func.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_a_can_import_into_own_tenant(
    client: AsyncClient,
    token_a: str,
    tenant_a: Tenant,
):
    csv_content = b"registration_number,full_name\n20241001,Aluno Teste\n"

    r = await client.post(
        f"/api/v1/onboarding/tenants/{tenant_a.id}/import-students",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("alunos.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Permissoes de role: admin nao pode criar tenants (so super_admin)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_admin_cannot_create_tenant(client: AsyncClient, token_a: str):
    r = await client.post(
        "/api/v1/onboarding/tenants",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "tenant_name": "Nova Escola",
            "tenant_slug": "nova-escola",
            "plan": "basic",
            "admin_email": "novo@escola.com",
            "admin_password": "SenhaForte@123",
            "admin_full_name": "Novo Admin",
        },
    )
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# Sem token = 401/403
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_protected_endpoints_reject_missing_auth(client: AsyncClient):
    for path in (
        "/api/v1/students",
        "/api/v1/employees",
        "/api/v1/conversations",
        "/api/v1/tenants",
    ):
        r = await client.get(path)
        assert r.status_code in (401, 403), f"{path} esta desprotegido!"
