# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.utils.security import decode_access_token

# ══════════════════════════════════════════════════════════════════════════════
# Database Engines
# ══════════════════════════════════════════════════════════════════════════════
#
# Two connection strategies:
#   1. APP engine  → connects as "igs_app" role → subject to RLS
#   2. WORKER engine → connects as "igs_worker" role → BYPASSRLS for batch tasks
#
# In dev/SQLite mode, both fall back to the single DATABASE_URL with no RLS.
# ══════════════════════════════════════════════════════════════════════════════

_is_postgres = "sqlite" not in settings.DATABASE_URL

_common_kwargs: dict = {"echo": settings.APP_DEBUG}
if _is_postgres:
    _common_kwargs.update(pool_pre_ping=True, pool_size=10, max_overflow=20)


def _build_rls_url() -> str:
    """Replace credentials in DATABASE_URL with igs_app role for RLS enforcement."""
    url = settings.DATABASE_URL
    if not _is_postgres:
        return url
    # Only swap if RLS_ENABLED is true and we have the standard format
    if not settings.RLS_ENABLED:
        return url
    # postgresql+asyncpg://user:pass@host:port/db → swap user:pass
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        replaced = parsed._replace(
            netloc=f"igs_app:{settings.RLS_APP_PASSWORD}@{parsed.hostname}"
            + (f":{parsed.port}" if parsed.port else "")
        )
        return urlunparse(replaced)
    except Exception:
        return url


def _build_worker_url() -> str:
    """Replace credentials in DATABASE_URL with igs_worker role (BYPASSRLS)."""
    url = settings.DATABASE_URL
    if not _is_postgres or not settings.RLS_ENABLED:
        return url
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        replaced = parsed._replace(
            netloc=f"igs_worker:{settings.RLS_WORKER_PASSWORD}@{parsed.hostname}"
            + (f":{parsed.port}" if parsed.port else "")
        )
        return urlunparse(replaced)
    except Exception:
        return url


# ── APP engine (RLS-enforced) ────────────────────────────────────────────────
engine = create_async_engine(_build_rls_url(), **_common_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── WORKER engine (BYPASSRLS for Celery batch tasks) ────────────────────────
worker_engine = create_async_engine(_build_worker_url(), **_common_kwargs)

WorkerSessionLocal = async_sessionmaker(
    worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ══════════════════════════════════════════════════════════════════════════════
# RLS: Inject tenant_id into PostgreSQL session variable
# ══════════════════════════════════════════════════════════════════════════════


async def _set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """Set app.current_tenant on the PostgreSQL connection for RLS filtering."""
    if _is_postgres and settings.RLS_ENABLED:
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": tenant_id},
        )


# ══════════════════════════════════════════════════════════════════════════════
# FastAPI Dependencies
# ══════════════════════════════════════════════════════════════════════════════


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session WITHOUT tenant context.

    Used by auth endpoints (login, register) that run before tenant is known.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_tenant(
    token_data: dict = Depends(lambda: None),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session WITH RLS tenant context injected.

    This is the primary session factory for tenant-scoped endpoints.
    Call via Depends(get_tenant_db) which wires token + session together.
    """
    # This is a template — actual wiring happens in get_tenant_db below
    yield  # type: ignore


async def get_tenant_db(
    token_data: dict = Depends(lambda: _get_current_user_id_dep()),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Inject tenant context into the session, then return it."""
    tenant_id = token_data.get("tenant_id") if token_data else None
    if tenant_id:
        await _set_tenant_context(db, str(tenant_id))
    return db


# ── Auth ─────────────────────────────────────────────────────────────────────

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# Alias for internal use
_get_current_user_id_dep = get_current_user_id


async def get_current_user(
    token_data: dict = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.user import User

    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")

    # Inject tenant context before querying
    tenant_id = token_data.get("tenant_id")
    if tenant_id:
        await _set_tenant_context(db, str(tenant_id))

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo")

    # Cross-valida tenant_id do token com o registro no DB (anti stale-token).
    # Se o usuário foi movido de tenant, tokens antigos com tenant_id desatualizado
    # são rejeitados — força re-login para refletir o estado atual.
    token_tenant = str(tenant_id) if tenant_id else None
    user_tenant = str(user.tenant_id) if user.tenant_id else None
    if token_tenant != user_tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token desatualizado (tenant alterado) — faça login novamente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*roles: str):
    """Factory de dependencia para verificar papeis do usuario."""

    async def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissao insuficiente",
            )
        return current_user

    return dependency


def get_tenant_id(
    token_data: dict = Depends(get_current_user_id),
) -> uuid.UUID | None:
    tenant_id = token_data.get("tenant_id")
    if tenant_id:
        return uuid.UUID(tenant_id)
    return None
