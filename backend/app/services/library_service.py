# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Serviço de Biblioteca — busca de acervo, empréstimos e renovações.
"""

import logging
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import Book, Loan

logger = logging.getLogger(__name__)

DEFAULT_LOAN_DAYS = 14
MAX_RENEWALS = 2


async def search_books(
    db: AsyncSession,
    tenant_id: UUID,
    query: str,
    category: Optional[str] = None,
    available_only: bool = False,
    limit: int = 10,
) -> list[Book]:
    """Busca livros no acervo por título, autor ou ISBN."""
    stmt = select(Book).where(
        Book.tenant_id == tenant_id,
        Book.is_active.is_(True),
    )

    search_pattern = f"%{query}%"
    stmt = stmt.where(
        (Book.title.ilike(search_pattern))
        | (Book.author.ilike(search_pattern))
        | (Book.isbn.ilike(search_pattern))
    )

    if category:
        stmt = stmt.where(Book.category.ilike(f"%{category}%"))

    if available_only:
        stmt = stmt.where(Book.available_copies > 0)

    stmt = stmt.order_by(Book.title).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_student_loans(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
    active_only: bool = True,
) -> list[Loan]:
    """Retorna empréstimos do aluno."""
    stmt = select(Loan).where(
        Loan.tenant_id == tenant_id,
        Loan.student_id == student_id,
    )
    if active_only:
        stmt = stmt.where(Loan.status.in_(["active", "overdue"]))

    stmt = stmt.order_by(Loan.due_date.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def renew_loan(
    db: AsyncSession,
    tenant_id: UUID,
    loan_id: UUID,
) -> dict:
    """Renova um empréstimo específico."""
    result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.tenant_id == tenant_id,
            Loan.status.in_(["active", "overdue"]),
        )
    )
    loan = result.scalar_one_or_none()
    if not loan:
        return {"success": False, "message": "Empréstimo não encontrado ou já devolvido."}

    if loan.renewals >= loan.max_renewals:
        return {
            "success": False,
            "message": (
                f"Limite de renovações atingido ({loan.max_renewals}). "
                "Por favor, devolva o livro na biblioteca."
            ),
        }

    loan.renewals += 1
    loan.due_date = date.today() + timedelta(days=DEFAULT_LOAN_DAYS)
    loan.status = "active"
    await db.flush()

    # Fetch book title for message
    book_result = await db.execute(select(Book).where(Book.id == loan.book_id))
    book = book_result.scalar_one_or_none()
    book_title = book.title if book else "Livro"

    return {
        "success": True,
        "loan_id": str(loan.id),
        "book_title": book_title,
        "new_due_date": str(loan.due_date),
        "renewals_used": loan.renewals,
        "renewals_remaining": loan.max_renewals - loan.renewals,
        "message": (
            f"Renovação realizada! '{book_title}' — "
            f"nova data de devolução: {loan.due_date.strftime('%d/%m/%Y')}. "
            f"Renovações restantes: {loan.max_renewals - loan.renewals}."
        ),
    }


async def renew_active_loans(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
) -> dict:
    """Renova todos os empréstimos ativos do aluno."""
    loans = await get_student_loans(db, tenant_id, student_id, active_only=True)
    if not loans:
        return {"success": False, "message": "Você não possui empréstimos ativos na biblioteca."}

    results = []
    errors = []
    for loan in loans:
        r = await renew_loan(db, tenant_id, loan.id)
        if r["success"]:
            results.append(r)
        else:
            errors.append(r["message"])

    if not results and errors:
        return {"success": False, "message": " | ".join(errors)}

    renewed_titles = [r["book_title"] for r in results]
    msg_parts = [f"✅ {t}" for t in renewed_titles]
    if errors:
        msg_parts.append(f"\n⚠️ Não renovados: {'; '.join(errors)}")

    return {
        "success": True,
        "renewed_count": len(results),
        "message": (f"Renovação realizada para {len(results)} livro(s):\n" + "\n".join(msg_parts)),
        "details": results,
    }


async def get_library_summary(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
) -> dict:
    """Resumo da situação na biblioteca: empréstimos ativos, atrasos, etc."""
    loans = await get_student_loans(db, tenant_id, student_id, active_only=True)

    today = date.today()
    active = []
    overdue = []

    for loan in loans:
        book_result = await db.execute(select(Book).where(Book.id == loan.book_id))
        book = book_result.scalar_one_or_none()
        item = {
            "book_title": book.title if book else "—",
            "due_date": str(loan.due_date),
            "renewals_used": loan.renewals,
            "renewals_remaining": loan.max_renewals - loan.renewals,
        }
        if loan.due_date < today:
            overdue.append(item)
            if loan.status != "overdue":
                loan.status = "overdue"
        else:
            active.append(item)

    await db.flush()

    return {
        "active_loans": active,
        "overdue_loans": overdue,
        "total_active": len(active),
        "total_overdue": len(overdue),
    }
