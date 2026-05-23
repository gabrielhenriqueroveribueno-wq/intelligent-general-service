# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KBArticle, KBCategory
from app.services import cache_service


async def search_articles(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    applies_to: Optional[str] = None,
    limit: int = 5,
) -> list[KBArticle]:
    """Busca artigos na KB por texto (full-text simples com ILIKE). Resultado cacheado 5 min."""
    cached = await cache_service.get_kb(tenant_id, query, applies_to)
    if cached is not None:
        # Retorna dados simples do cache (sem ORM objects para não poluir a session)
        return cached  # type: ignore[return-value]

    q = select(KBArticle).where(
        KBArticle.tenant_id == tenant_id,
        KBArticle.is_published,
        or_(
            KBArticle.title.ilike(f"%{query}%"),
            KBArticle.content.ilike(f"%{query}%"),
        ),
    )

    if applies_to and applies_to != "all":
        q = q.where(or_(KBArticle.applies_to == applies_to, KBArticle.applies_to == "all"))

    result = await db.execute(q.order_by(KBArticle.usage_count.desc()).limit(limit))
    articles = result.scalars().all()

    # Incrementa contador de uso
    for article in articles:
        article.usage_count += 1

    # Serializa para cache (apenas campos necessários para o AI service)
    serialized = [
        {"title": a.title, "content": a.content, "applies_to": a.applies_to} for a in articles
    ]
    await cache_service.set_kb(tenant_id, query, applies_to, serialized)

    return articles


async def list_articles(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category_id: Optional[uuid.UUID] = None,
    applies_to: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[KBArticle], int]:
    query = select(KBArticle).where(KBArticle.tenant_id == tenant_id, KBArticle.is_published)
    if category_id:
        query = query.where(KBArticle.category_id == category_id)
    if applies_to:
        query = query.where(KBArticle.applies_to == applies_to)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def create_article(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    title: str,
    content: str,
    applies_to: str = "all",
    keywords: Optional[list] = None,
    category_id: Optional[uuid.UUID] = None,
) -> KBArticle:
    article = KBArticle(
        tenant_id=tenant_id,
        title=title,
        content=content,
        applies_to=applies_to,
        keywords=keywords or [],
        category_id=category_id,
    )
    db.add(article)
    await db.flush()
    await cache_service.invalidate_kb(tenant_id)
    return article


async def list_categories(db: AsyncSession, tenant_id: uuid.UUID) -> list[KBCategory]:
    result = await db.execute(
        select(KBCategory)
        .where(KBCategory.tenant_id == tenant_id)
        .order_by(KBCategory.sort_order, KBCategory.name)
    )
    return result.scalars().all()
