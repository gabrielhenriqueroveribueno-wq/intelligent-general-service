import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserMe
from app.services.auth_service import authenticate_user, refresh_tokens

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await authenticate_user(db, body.email, body.password)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, new_refresh = await refresh_tokens(db, body.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.get("/me", response_model=UserMe)
async def me(current_user=Depends(get_current_user)):
    return UserMe(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
    )


# ── Self-service Signup ───────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    institution_name: str
    slug: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    phone: str = ""


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{2,98}[a-z0-9]$")


@router.post("/signup", status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Cria novo tenant + admin em plano trial (14 dias)."""
    from datetime import datetime, timedelta, timezone

    from app.models.tenant import Tenant
    from app.models.user import User
    from app.utils.security import hash_password

    if not _SLUG_RE.match(body.slug):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Slug inválido. Use apenas letras minúsculas, números e hifens (3-100 chars).",
        )

    if len(body.admin_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Senha deve ter pelo menos 8 caracteres.",
        )

    # Slug único
    existing_slug = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este identificador já está em uso. Tente outro.",
        )

    # Email único
    existing_email = await db.execute(select(User).where(User.email == body.admin_email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    tenant = Tenant(
        name=body.institution_name,
        slug=body.slug,
        whatsapp_phone=body.phone or None,
        plan="trial",
        is_active=True,
        settings={"trial_ends_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()},
    )
    db.add(tenant)
    await db.flush()

    admin = User(
        tenant_id=tenant.id,
        full_name=body.admin_name,
        email=body.admin_email,
        hashed_password=hash_password(body.admin_password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    await db.commit()

    # Envia email de boas-vindas (falha silenciosamente se SMTP não configurado)
    try:
        from app.services.email_service import send_email
        from app.services.email_templates import welcome as welcome_tpl

        send_email(
            to=body.admin_email,
            subject=f"Bem-vindo ao IGS — {body.institution_name}",
            body=welcome_tpl(body.institution_name, body.admin_name),
        )
    except Exception:
        pass

    return {
        "message": "Conta criada com sucesso! Trial de 14 dias ativo.",
        "tenant_id": str(tenant.id),
        "slug": tenant.slug,
    }
