import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.models.knowledge_base import KBArticle, KBCategory
from app.services import knowledge_service
from app.utils.exceptions import NotFoundError


class ArticleCreate(BaseModel):
    title: str
    content: str
    applies_to: str = "all"
    keywords: Optional[list] = None
    category_id: Optional[uuid.UUID] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    applies_to: Optional[str] = None
    keywords: Optional[list] = None
    is_published: Optional[bool] = None


class ArticleResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    applies_to: str
    keywords: Optional[list]
    is_published: bool
    usage_count: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[uuid.UUID] = None
    sort_order: int = 0


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID]
    sort_order: int

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    categories = await knowledge_service.list_categories(db, tenant_id)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    cat = KBCategory(tenant_id=tenant_id, **body.model_dump())
    db.add(cat)
    await db.flush()
    return CategoryResponse.model_validate(cat)


@router.get("/articles", response_model=list[ArticleResponse])
async def list_articles(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    applies_to: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    if search:
        articles = await knowledge_service.search_articles(db, tenant_id, search, applies_to)
    else:
        articles, _ = await knowledge_service.list_articles(
            db, tenant_id, applies_to=applies_to, page=page, size=size
        )
    return [ArticleResponse.model_validate(a) for a in articles]


@router.post("/articles", response_model=ArticleResponse, status_code=201)
async def create_article(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    article = await knowledge_service.create_article(
        db, tenant_id, body.title, body.content, body.applies_to, body.keywords, body.category_id
    )
    return ArticleResponse.model_validate(article)


@router.patch("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: uuid.UUID,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    from sqlalchemy import select

    result = await db.execute(
        select(KBArticle).where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Artigo")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(article, field, value)
    return ArticleResponse.model_validate(article)


@router.delete("/articles/{article_id}", status_code=204)
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager")),
):
    from sqlalchemy import select

    result = await db.execute(
        select(KBArticle).where(KBArticle.id == article_id, KBArticle.tenant_id == tenant_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Artigo")
    await db.delete(article)
