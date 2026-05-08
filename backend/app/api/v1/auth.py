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
    access_token, refresh_token, must_change = await authenticate_user(db, body.email, body.password)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=must_change,
    )


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
        must_change_password=current_user.must_change_password,
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", status_code=200)
async def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Troca a senha do usuário autenticado. Limpa must_change_password se aplicável."""
    from app.utils.security import hash_password, verify_password

    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=422, detail="Nova senha deve ter pelo menos 8 caracteres")

    from sqlalchemy import update as sql_update

    await db.execute(
        sql_update(type(current_user))
        .where(type(current_user).id == current_user.id)
        .values(
            password_hash=hash_password(body.new_password),
            must_change_password=False,
        )
    )
    await db.commit()
    return {"message": "Senha alterada com sucesso"}


@router.delete("/me", status_code=200)
async def delete_me(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Anonimiza e desativa a conta do usuário autenticado (LGPD Art. 18).
    Não remove o registro para preservar integridade referencial — apenas anonimiza os dados pessoais.
    """
    import uuid as _uuid
    from sqlalchemy import update as sql_update

    anon_suffix = str(_uuid.uuid4())[:8]
    await db.execute(
        sql_update(type(current_user))
        .where(type(current_user).id == current_user.id)
        .values(
            email=f"deleted_{anon_suffix}@removed.invalid",
            full_name="[Conta removida]",
            password_hash="",
            is_active=False,
        )
    )
    await db.commit()
    return {"message": "Conta removida conforme solicitado (LGPD Art. 18)"}


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
        password_hash=hash_password(body.admin_password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    await db.commit()

    # Envia email de boas-vindas (falha silenciosamente se SMTP não configurado)
    try:
        from app.services.email_service import send_email_async
        from app.services.email_templates import welcome as welcome_tpl

        await send_email_async(
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
