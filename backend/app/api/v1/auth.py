import re

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserMe
from app.services import audit_service
from app.services.auth_service import authenticate_user, refresh_tokens
from app.utils.exceptions import UnauthorizedError

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = audit_service.extract_ip(request)
    try:
        access_token, refresh_token, must_change, user = await authenticate_user(
            db, body.email, body.password
        )
    except UnauthorizedError:
        # Login falhou — registra em transação isolada para sobreviver ao rollback.
        # Email é mantido para forensics (já é PII conhecido pelo atacante).
        await audit_service.log_event_isolated(
            action=audit_service.ACTION_LOGIN_FAILED,
            details={"email": body.email},
            ip=ip,
        )
        raise

    # Audit log atômico com last_login_at — get_db comita ambos juntos.
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_LOGIN_SUCCESS,
        tenant_id=user.tenant_id,
        user_id=user.id,
        ip=ip,
    )
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
    request: Request,
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
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_PASSWORD_CHANGED,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        ip=audit_service.extract_ip(request),
    )
    await db.commit()
    return {"message": "Senha alterada com sucesso"}


@router.get("/me/export")
async def export_me(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    LGPD Art. 18 — Portabilidade: exporta todos os dados pessoais do usuário autenticado
    em formato JSON legível por máquina.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.ticket import Ticket

    # Tickets do usuário (se for agente atribuído)
    tickets_q = await db.execute(
        select(Ticket)
        .where(Ticket.tenant_id == current_user.tenant_id)
        .where(Ticket.assigned_to == current_user.id)
        .limit(500)
    )
    tickets = [
        {
            "id": str(t.id),
            "subject": t.subject,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets_q.scalars().all()
    ]

    export = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "data_controller": "IGS — Intelligent General Service",
        "legal_basis": "LGPD Art. 18, inciso V — Portabilidade dos dados",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at.isoformat()
            if current_user.last_login_at
            else None,
            "created_at": current_user.created_at.isoformat()
            if hasattr(current_user, "created_at") and current_user.created_at
            else None,
        },
        "tickets_assigned": tickets,
    }

    from fastapi.responses import JSONResponse

    await audit_service.log_event(
        db,
        action=audit_service.ACTION_DATA_EXPORTED,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        ip=audit_service.extract_ip(request),
        details={"tickets_count": len(tickets)},
    )
    await db.commit()

    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f'attachment; filename="igs-dados-{current_user.id}.json"',
            "Content-Type": "application/json; charset=utf-8",
        },
    )


@router.delete("/me", status_code=200)
async def delete_me(
    request: Request,
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
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_ACCOUNT_DELETED,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        ip=audit_service.extract_ip(request),
        details={"reason": "lgpd_art_18_user_request"},
    )
    await db.commit()
    return {"message": "Conta removida conforme solicitado (LGPD Art. 18)"}


# ── Password Recovery ────────────────────────────────────────────────────────


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password", status_code=202)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Envia email com link de reset de senha.
    Retorna 202 sempre (não revela se o email existe).
    """
    import secrets

    import redis.asyncio as aioredis

    from app.models.user import User

    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if user:
        token = secrets.token_urlsafe(32)
        redis_client = aioredis.from_url(settings.REDIS_URL.replace("/0", "/4"))
        try:
            await redis_client.setex(f"pwd_reset:{token}", 1800, str(user.id))
        finally:
            await redis_client.aclose()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        try:
            from app.services.email_service import send_email_async
            from app.services.email_templates import password_reset as reset_tpl

            await send_email_async(
                to=user.email,
                subject="Redefinição de senha — IGS",
                body=reset_tpl(user.full_name, reset_url),
            )
        except Exception:
            pass

        await audit_service.log_event(
            db,
            action=audit_service.ACTION_PASSWORD_RESET_REQUESTED,
            tenant_id=user.tenant_id,
            user_id=user.id,
            ip=audit_service.extract_ip(request),
        )

    return {"message": "Se o email existir, você receberá as instruções em breve."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password", status_code=200)
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Redefine a senha usando o token recebido por email."""
    import redis.asyncio as aioredis

    from app.models.user import User
    from app.utils.security import hash_password

    if len(body.new_password) < 8:
        raise HTTPException(status_code=422, detail="Senha deve ter pelo menos 8 caracteres.")

    redis_client = aioredis.from_url(settings.REDIS_URL.replace("/0", "/4"))
    try:
        user_id = await redis_client.get(f"pwd_reset:{body.token}")
        if not user_id:
            raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
        await redis_client.delete(f"pwd_reset:{body.token}")
    finally:
        await redis_client.aclose()

    import uuid

    from sqlalchemy import update as sql_update

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id.decode())))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário não encontrado.")

    await db.execute(
        sql_update(User)
        .where(User.id == user.id)
        .values(password_hash=hash_password(body.new_password), must_change_password=False)
    )
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_PASSWORD_RESET_COMPLETED,
        tenant_id=user.tenant_id,
        user_id=user.id,
        ip=audit_service.extract_ip(request),
    )
    await db.commit()
    return {"message": "Senha redefinida com sucesso. Você já pode fazer login."}


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
async def signup(body: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)):
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
    await db.flush()

    ip = audit_service.extract_ip(request)
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_TENANT_CREATED,
        tenant_id=tenant.id,
        entity_type="tenant",
        entity_id=tenant.id,
        details={"slug": tenant.slug, "plan": "trial"},
        ip=ip,
    )
    await audit_service.log_event(
        db,
        action=audit_service.ACTION_USER_CREATED,
        tenant_id=tenant.id,
        user_id=admin.id,
        entity_type="user",
        entity_id=admin.id,
        details={"role": "admin", "via": "signup"},
        ip=ip,
    )
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
