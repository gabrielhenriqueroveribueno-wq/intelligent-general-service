"""
Endpoints para gerenciamento de templates de mensagem WhatsApp (HSM).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.notification import MessageTemplate
from app.utils.exceptions import NotFoundError

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    meta_template_name: str
    language_code: str = "pt_BR"
    category: str = "UTILITY"
    parameters_schema: Optional[dict] = None


class TemplateSendRequest(BaseModel):
    to: str  # Número de telefone destino
    components: Optional[list] = None  # Componentes com parâmetros


@router.get("")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    query = select(MessageTemplate).where(
        MessageTemplate.tenant_id == tenant_id,
        MessageTemplate.is_active == True,
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * size).limit(size))
    templates = result.scalars().all()
    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "meta_template_name": t.meta_template_name,
                "language_code": t.language_code,
                "category": t.category,
                "parameters_schema": t.parameters_schema,
            }
            for t in templates
        ],
        "total": total,
    }


@router.post("", status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin")),
):
    template = MessageTemplate(
        tenant_id=tenant_id,
        name=body.name,
        meta_template_name=body.meta_template_name,
        language_code=body.language_code,
        category=body.category,
        parameters_schema=body.parameters_schema or {},
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return {"id": str(template.id), "name": template.name}


@router.post("/{template_id}/send", status_code=202)
async def send_template(
    template_id: uuid.UUID,
    body: TemplateSendRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    """Envia um template para um número de telefone específico."""
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    result = await db.execute(
        select(MessageTemplate).where(
            MessageTemplate.id == template_id,
            MessageTemplate.tenant_id == tenant_id,
            MessageTemplate.is_active == True,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundError("Template")

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
        return {"error": "Tenant sem configuração WhatsApp"}

    msg_id = await whatsapp_service.send_template_message(
        phone_number_id=tenant.whatsapp_phone_number_id,
        access_token=tenant.whatsapp_token,
        to=body.to,
        template_name=template.meta_template_name,
        language_code=template.language_code,
        components=body.components,
    )

    return {"message_id": msg_id, "status": "sent" if msg_id else "failed"}
