"""
Endpoints de onboarding de novos clientes.

Fluxo suportado:
1. super_admin cria tenant + admin user → POST /api/v1/onboarding/tenants
2. admin do tenant (ou super_admin) faz upload CSV de alunos/funcionarios
3. admin configura WhatsApp + Claude API via tenants/settings existente

Todas as rotas sob /api/v1/onboarding/...
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.services import onboarding_service

logger = logging.getLogger(__name__)

router = APIRouter()


MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB


# ══════════════════════════════════════════════════════════════════════════════
# Request / response schemas
# ══════════════════════════════════════════════════════════════════════════════


class CreateTenantWithAdminRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=255)
    tenant_slug: str = Field(min_length=3, max_length=64)
    plan: str = Field(default="basic")
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=72)
    admin_full_name: str = Field(min_length=2, max_length=255)
    bot_name: Optional[str] = Field(default=None, max_length=100)
    welcome_message: Optional[str] = Field(default=None, max_length=2000)
    business_hours_start: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    business_hours_end: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class CreateTenantWithAdminResponse(BaseModel):
    tenant_id: uuid.UUID
    slug: str
    admin_email: str
    admin_user_id: uuid.UUID
    login_url: str


class ImportResponse(BaseModel):
    created: int
    skipped: int
    errors: list[str]


# ══════════════════════════════════════════════════════════════════════════════
# Tenant + admin creation (super_admin only)
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/tenants",
    response_model=CreateTenantWithAdminResponse,
    status_code=201,
)
async def create_tenant_with_admin(
    body: CreateTenantWithAdminRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
) -> CreateTenantWithAdminResponse:
    try:
        result = await onboarding_service.create_tenant_with_admin(
            db,
            tenant_name=body.tenant_name,
            tenant_slug=body.tenant_slug,
            plan=body.plan,
            admin_email=body.admin_email,
            admin_password=body.admin_password,
            admin_full_name=body.admin_full_name,
            bot_name=body.bot_name,
            welcome_message=body.welcome_message,
            business_hours_start=body.business_hours_start,
            business_hours_end=body.business_hours_end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()

    return CreateTenantWithAdminResponse(
        tenant_id=result.tenant_id,
        slug=result.slug,
        admin_email=result.admin_email,
        admin_user_id=result.admin_user_id,
        login_url="/login",
    )


# ══════════════════════════════════════════════════════════════════════════════
# CSV import — students
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/tenants/{target_tenant_id}/import-students",
    response_model=ImportResponse,
)
async def import_students(
    target_tenant_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin")),
) -> ImportResponse:
    _assert_can_access_tenant(user, current_tenant_id, target_tenant_id)

    content = await _read_upload(file)

    try:
        result = await onboarding_service.import_students_from_csv(
            db, target_tenant_id, content
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    return ImportResponse(
        created=result.created,
        skipped=result.skipped,
        errors=result.errors,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CSV import — employees
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/tenants/{target_tenant_id}/import-employees",
    response_model=ImportResponse,
)
async def import_employees(
    target_tenant_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin")),
) -> ImportResponse:
    _assert_can_access_tenant(user, current_tenant_id, target_tenant_id)

    content = await _read_upload(file)

    try:
        result = await onboarding_service.import_employees_from_csv(
            db, target_tenant_id, content
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    return ImportResponse(
        created=result.created,
        skipped=result.skipped,
        errors=result.errors,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CSV template downloads
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/templates/students.csv")
async def download_students_template(
    _=Depends(require_roles("super_admin", "admin")),
) -> Response:
    csv_content = onboarding_service.generate_students_csv_template()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="template_alunos.csv"'},
    )


@router.get("/templates/employees.csv")
async def download_employees_template(
    _=Depends(require_roles("super_admin", "admin")),
) -> Response:
    csv_content = onboarding_service.generate_employees_csv_template()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="template_funcionarios.csv"'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _assert_can_access_tenant(user, current_tenant_id, target_tenant_id) -> None:
    """
    Regras:
    - super_admin: qualquer tenant
    - admin: apenas o proprio tenant
    """
    role = getattr(user, "role", None) if user else None
    if role == "super_admin":
        return
    if target_tenant_id != current_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Voce nao tem permissao para importar dados em outro tenant",
        )


async def _read_upload(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo deve ter extensao .csv")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {MAX_CSV_BYTES // (1024 * 1024)} MB",
        )
    return content
