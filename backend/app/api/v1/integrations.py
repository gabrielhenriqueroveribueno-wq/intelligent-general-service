"""
Endpoints para gerenciar integracoes com sistemas academicos.

Rotas:
- GET    /api/v1/integrations/providers          → catalogo de providers
- GET    /api/v1/integrations                    → lista integracoes do tenant
- POST   /api/v1/integrations                    → cria
- PATCH  /api/v1/integrations/{id}               → atualiza (config / credenciais / status)
- DELETE /api/v1/integrations/{id}               → remove
- POST   /api/v1/integrations/{id}/test          → testa conexao (sem sincronizar)
- POST   /api/v1/integrations/{id}/sync-now      → dispara sync imediata
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.academic_integration import AcademicIntegration
from app.services.integrations.registry import (
    PROVIDER_CATALOG,
    decrypt_credentials,
    encrypt_credentials,
    get_integrator,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════


ProviderType = Literal["sophia", "totvs", "generic_rest"]
StatusType = Literal["pending", "active", "paused", "error"]


class IntegrationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    provider_type: ProviderType
    config: dict = Field(default_factory=dict)
    credentials: dict = Field(default_factory=dict)
    sync_cron: str = "0 */6 * * *"


class IntegrationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    config: Optional[dict] = None
    credentials: Optional[dict] = None  # se nao None, sobrescreve
    sync_cron: Optional[str] = None
    status: Optional[StatusType] = None


class IntegrationResponse(BaseModel):
    id: uuid.UUID
    name: str
    provider_type: str
    config: dict
    has_credentials: bool
    status: str
    sync_cron: str
    last_sync_at: Optional[datetime]
    last_sync_duration_ms: Optional[int]
    last_sync_records_synced: Optional[int]
    last_sync_error: Optional[str]
    created_at: datetime


def _to_response(integ: AcademicIntegration) -> IntegrationResponse:
    return IntegrationResponse(
        id=integ.id,
        name=integ.name,
        provider_type=integ.provider_type,
        config=integ.config or {},
        has_credentials=bool(integ.credentials_encrypted),
        status=integ.status,
        sync_cron=integ.sync_cron,
        last_sync_at=integ.last_sync_at,
        last_sync_duration_ms=integ.last_sync_duration_ms,
        last_sync_records_synced=integ.last_sync_records_synced,
        last_sync_error=integ.last_sync_error,
        created_at=integ.created_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/providers")
async def list_providers(
    _=Depends(require_roles("super_admin", "admin")),
) -> list[dict]:
    """Catalogo de providers + campos esperados (para o frontend)."""
    return PROVIDER_CATALOG


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> list[IntegrationResponse]:
    result = await db.execute(
        select(AcademicIntegration)
        .where(AcademicIntegration.tenant_id == tenant_id)
        .order_by(AcademicIntegration.created_at.desc())
    )
    return [_to_response(i) for i in result.scalars().all()]


@router.post("", response_model=IntegrationResponse, status_code=201)
async def create_integration(
    body: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> IntegrationResponse:
    # Verifica duplicidade por (tenant, provider)
    existing = await db.execute(
        select(AcademicIntegration).where(
            AcademicIntegration.tenant_id == tenant_id,
            AcademicIntegration.provider_type == body.provider_type,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Ja existe integracao do tipo '{body.provider_type}' para este tenant",
        )

    integ = AcademicIntegration(
        tenant_id=tenant_id,
        name=body.name.strip(),
        provider_type=body.provider_type,
        config=body.config,
        sync_cron=body.sync_cron,
        status="pending",
    )
    if body.credentials:
        integ.credentials_encrypted = encrypt_credentials(body.credentials)

    db.add(integ)
    await db.commit()
    await db.refresh(integ)
    return _to_response(integ)


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: uuid.UUID,
    body: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> IntegrationResponse:
    integ = await _load(db, integration_id, tenant_id)

    update_data = body.model_dump(exclude_unset=True)

    # Credentials precisa ser tratado a parte (criptografar)
    if "credentials" in update_data:
        creds = update_data.pop("credentials")
        if creds:
            integ.credentials_encrypted = encrypt_credentials(creds)

    for field, value in update_data.items():
        if value is not None:
            setattr(integ, field, value)

    await db.commit()
    await db.refresh(integ)
    return _to_response(integ)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    integ = await _load(db, integration_id, tenant_id)
    await db.delete(integ)
    await db.commit()
    return {"success": True}


@router.post("/{integration_id}/test")
async def test_connection(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Testa conexao sem sincronizar (validacao da config + credenciais)."""
    integ = await _load(db, integration_id, tenant_id)
    creds = decrypt_credentials(integ.credentials_encrypted)

    try:
        integrator = get_integrator(integ.provider_type, integ.config, creds)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ok, message = await integrator.test_connection()
    return {"success": ok, "message": message}


@router.post("/{integration_id}/sync-now")
async def sync_now(
    integration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
) -> dict:
    """Dispara sync imediata via Celery (assincrona)."""
    integ = await _load(db, integration_id, tenant_id)

    from app.tasks.integration_sync_tasks import run_integration_sync_task

    run_integration_sync_task.delay(str(integ.id))
    return {
        "success": True,
        "message": "Sincronizacao agendada — acompanhe o progresso pelo status",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


async def _load(
    db: AsyncSession, integration_id: uuid.UUID, tenant_id: uuid.UUID
) -> AcademicIntegration:
    result = await db.execute(
        select(AcademicIntegration).where(
            AcademicIntegration.id == integration_id,
            AcademicIntegration.tenant_id == tenant_id,
        )
    )
    integ = result.scalar_one_or_none()
    if not integ:
        raise HTTPException(status_code=404, detail="Integracao nao encontrada")
    return integ
