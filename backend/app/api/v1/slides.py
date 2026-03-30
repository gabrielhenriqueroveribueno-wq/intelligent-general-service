"""
Endpoints para geração e gerenciamento de slides via IA.

Professores (role=teacher) podem gerar, atualizar e listar apresentações.
Admins podem gerenciar templates.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.slide import SlideGenerationLog, SlidePresentation, SlideTemplate
from app.schemas.slide import (
    SlideGenerateRequest,
    SlideGenerationLogResponse,
    SlidePresentationListResponse,
    SlidePresentationResponse,
    SlideTemplateCreate,
    SlideTemplateResponse,
    SlideTemplateUpdate,
    SlideUpdateRequest,
)
from app.services.slide_service import generate_slides, update_slides

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Templates ────────────────────────────────────────────────────────────────


@router.get("/templates", response_model=list[SlideTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    _user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Lista templates de slides disponíveis para o tenant."""
    result = await db.execute(
        select(SlideTemplate)
        .where(SlideTemplate.tenant_id == tenant_id)
        .order_by(SlideTemplate.is_default.desc(), SlideTemplate.name)
    )
    return result.scalars().all()


@router.post(
    "/templates",
    response_model=SlideTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    data: SlideTemplateCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    _user=Depends(require_roles("super_admin", "admin")),
):
    """Cria um novo template de slides (admin only)."""
    if data.is_default:
        # Remove is_default de outros templates do tenant
        existing = await db.execute(
            select(SlideTemplate).where(
                SlideTemplate.tenant_id == tenant_id,
                SlideTemplate.is_default.is_(True),
            )
        )
        for t in existing.scalars().all():
            t.is_default = False

    template = SlideTemplate(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        template_rules=data.template_rules,
        example_content=data.example_content,
        is_default=data.is_default,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


@router.patch("/templates/{template_id}", response_model=SlideTemplateResponse)
async def update_template(
    template_id: UUID,
    data: SlideTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    _user=Depends(require_roles("super_admin", "admin")),
):
    """Atualiza um template existente (admin only)."""
    result = await db.execute(
        select(SlideTemplate).where(
            SlideTemplate.id == template_id,
            SlideTemplate.tenant_id == tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        existing = await db.execute(
            select(SlideTemplate).where(
                SlideTemplate.tenant_id == tenant_id,
                SlideTemplate.is_default.is_(True),
                SlideTemplate.id != template_id,
            )
        )
        for t in existing.scalars().all():
            t.is_default = False

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return template


# ── Geração de Slides ────────────────────────────────────────────────────────


@router.post(
    "/generate",
    response_model=SlidePresentationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_presentation(
    data: SlideGenerateRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Gera uma nova apresentação de slides via IA."""
    try:
        presentation = await generate_slides(
            db=db,
            tenant_id=tenant_id,
            teacher_id=user.id,
            prompt=data.prompt,
            subject=data.subject,
            template_id=data.template_id,
            num_slides=data.num_slides,
        )
        await db.flush()
        await db.refresh(presentation)
        return presentation
    except Exception as e:
        logger.exception("Erro ao gerar slides: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar slides: {str(e)}",
        )


# ── Apresentações ────────────────────────────────────────────────────────────


@router.get("/presentations", response_model=SlidePresentationListResponse)
async def list_presentations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    subject: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Lista apresentações do professor (ou todas para admin)."""
    query = select(SlidePresentation).where(SlidePresentation.tenant_id == tenant_id)

    # Professores veem apenas suas apresentações
    if user.role == "teacher":
        query = query.where(SlidePresentation.teacher_id == user.id)

    if subject:
        query = query.where(SlidePresentation.subject.ilike(f"%{subject}%"))

    # Total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginação
    result = await db.execute(
        query.order_by(SlidePresentation.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = result.scalars().all()

    return SlidePresentationListResponse(items=items, total=total, page=page, size=size)


@router.get("/presentations/{presentation_id}", response_model=SlidePresentationResponse)
async def get_presentation(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Retorna uma apresentação específica."""
    query = select(SlidePresentation).where(
        SlidePresentation.id == presentation_id,
        SlidePresentation.tenant_id == tenant_id,
    )
    if user.role == "teacher":
        query = query.where(SlidePresentation.teacher_id == user.id)

    result = await db.execute(query)
    presentation = result.scalar_one_or_none()
    if not presentation:
        raise HTTPException(status_code=404, detail="Apresentação não encontrada")
    return presentation


@router.patch("/presentations/{presentation_id}", response_model=SlidePresentationResponse)
async def update_presentation(
    presentation_id: UUID,
    data: SlideUpdateRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Atualiza slides existentes via novo prompt para a IA."""
    query = select(SlidePresentation).where(
        SlidePresentation.id == presentation_id,
        SlidePresentation.tenant_id == tenant_id,
    )
    if user.role == "teacher":
        query = query.where(SlidePresentation.teacher_id == user.id)

    result = await db.execute(query)
    presentation = result.scalar_one_or_none()
    if not presentation:
        raise HTTPException(status_code=404, detail="Apresentação não encontrada")

    try:
        updated = await update_slides(
            db=db,
            presentation=presentation,
            prompt=data.prompt,
            tenant_id=tenant_id,
            teacher_id=user.id,
        )
        await db.flush()
        await db.refresh(updated)
        return updated
    except Exception as e:
        logger.exception("Erro ao atualizar slides: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar slides: {str(e)}",
        )


# ── Histórico ────────────────────────────────────────────────────────────────


@router.get(
    "/presentations/{presentation_id}/history",
    response_model=list[SlideGenerationLogResponse],
)
async def get_generation_history(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user=Depends(require_roles("super_admin", "admin", "manager", "teacher")),
):
    """Retorna histórico de gerações/atualizações de uma apresentação."""
    # Verifica acesso à apresentação
    pres_query = select(SlidePresentation.id).where(
        SlidePresentation.id == presentation_id,
        SlidePresentation.tenant_id == tenant_id,
    )
    if user.role == "teacher":
        pres_query = pres_query.where(SlidePresentation.teacher_id == user.id)

    exists = await db.scalar(pres_query)
    if not exists:
        raise HTTPException(status_code=404, detail="Apresentação não encontrada")

    result = await db.execute(
        select(SlideGenerationLog)
        .where(SlideGenerationLog.presentation_id == presentation_id)
        .order_by(SlideGenerationLog.created_at.desc())
    )
    return result.scalars().all()
