import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.tenant import Tenant, TenantSettings
from app.schemas.tenant import (
    TenantCreate,
    TenantResponse,
    TenantSettingsResponse,
    TenantSettingsUpdate,
    TenantUpdate,
)
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Slug '{body.slug}' já está em uso")

    tenant = Tenant(**body.model_dump())
    db.add(tenant)
    await db.flush()
    return tenant


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    result = await db.execute(select(Tenant).order_by(Tenant.name))
    return result.scalars().all()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin", "admin")),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise NotFoundError("Tenant")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("super_admin")),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise NotFoundError("Tenant")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tenant, field, value)

    await db.flush()
    return tenant


@router.get("/settings/current", response_model=TenantSettingsResponse)
async def get_current_settings(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
):
    """Retorna configurações do tenant atual."""
    result = await db.execute(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
    ts = result.scalar_one_or_none()

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if not ts:
        return TenantSettingsResponse(
            has_whatsapp_config=bool(tenant and tenant.whatsapp_phone_number_id),
            has_ai_key=bool(tenant and tenant.claude_api_key),
        )

    return TenantSettingsResponse(
        bot_name=ts.bot_name,
        welcome_message=ts.welcome_message,
        business_hours_start=ts.business_hours_start,
        business_hours_end=ts.business_hours_end,
        out_of_hours_message=ts.out_of_hours_message,
        has_whatsapp_config=bool(tenant and tenant.whatsapp_phone_number_id),
        has_ai_key=bool(tenant and tenant.claude_api_key),
    )


@router.put("/settings/current", response_model=TenantSettingsResponse)
async def update_current_settings(
    body: TenantSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
):
    """Atualiza configurações do tenant atual."""
    result = await db.execute(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
    ts = result.scalar_one_or_none()

    if not ts:
        ts = TenantSettings(tenant_id=tenant_id)
        db.add(ts)

    # Update TenantSettings fields
    settings_fields = {
        "bot_name",
        "welcome_message",
        "business_hours_start",
        "business_hours_end",
        "out_of_hours_message",
    }
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in settings_fields:
            setattr(ts, field, value)

    # Update Tenant-level integration keys
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if tenant:
        if "whatsapp_phone_number_id" in update_data:
            tenant.whatsapp_phone_number_id = update_data["whatsapp_phone_number_id"]
        if "whatsapp_token" in update_data:
            tenant.whatsapp_token = update_data["whatsapp_token"]
        if "claude_api_key" in update_data:
            tenant.claude_api_key = update_data["claude_api_key"]

    await db.flush()

    return TenantSettingsResponse(
        bot_name=ts.bot_name,
        welcome_message=ts.welcome_message,
        business_hours_start=ts.business_hours_start,
        business_hours_end=ts.business_hours_end,
        out_of_hours_message=ts.out_of_hours_message,
        has_whatsapp_config=bool(tenant and tenant.whatsapp_phone_number_id),
        has_ai_key=bool(tenant and tenant.claude_api_key),
    )
