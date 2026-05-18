"""
Rotas públicas para captura de leads comerciais.

POST /leads        — Salva lead e envia email de notificação para o time comercial
GET  /leads        — Lista leads (admin only)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.lead import Lead

router = APIRouter()
logger = logging.getLogger(__name__)

COMMERCIAL_EMAIL = "comercial@igs.com.br"


class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    institution: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
    source: str = "landing"
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


@router.post("", status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Captura lead e notifica time comercial por email."""
    lead = Lead(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        institution=payload.institution,
        role=payload.role,
        message=payload.message,
        source=payload.source,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
    )
    db.add(lead)
    await db.flush()
    await db.commit()

    # Notifica time comercial
    try:
        from app.services.email_service import send_email_async

        body = (
            f"<h2>Novo lead capturado!</h2>"
            f"<table>"
            f"<tr><td><b>Nome:</b></td><td>{payload.name}</td></tr>"
            f"<tr><td><b>Email:</b></td><td>{payload.email}</td></tr>"
            f"<tr><td><b>Telefone:</b></td><td>{payload.phone or '—'}</td></tr>"
            f"<tr><td><b>Instituição:</b></td><td>{payload.institution or '—'}</td></tr>"
            f"<tr><td><b>Cargo:</b></td><td>{payload.role or '—'}</td></tr>"
            f"<tr><td><b>Mensagem:</b></td><td>{payload.message or '—'}</td></tr>"
            f"<tr><td><b>Fonte:</b></td><td>{payload.source}</td></tr>"
            f"</table>"
        )
        await send_email_async(
            to=COMMERCIAL_EMAIL,
            subject=f"Novo lead IGS: {payload.name} ({payload.institution or payload.email})",
            body=body,
        )
    except Exception as exc:
        logger.warning("Falha ao notificar lead por email: %s", exc)

    return {"success": True, "id": str(lead.id)}


@router.get("")
async def list_leads(
    page: int = 1,
    size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Lista leads (proteger com auth no router se necessário)."""
    from app.models.lead import Lead as LeadModel

    result = await db.execute(
        select(LeadModel)
        .order_by(LeadModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    leads = result.scalars().all()
    return {
        "items": [
            {
                "id": str(l.id),
                "name": l.name,
                "email": l.email,
                "phone": l.phone,
                "institution": l.institution,
                "role": l.role,
                "message": l.message,
                "source": l.source,
                "contacted": l.contacted,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in leads
        ]
    }
