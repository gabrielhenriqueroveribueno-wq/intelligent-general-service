# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.exceptions import UnauthorizedError
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> tuple[str, str, bool, User]:
    """Autentica o usuário e retorna (access_token, refresh_token, must_change_password, user)."""
    result = await db.execute(select(User).where(User.email == email, User.is_active))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Email ou senha incorretos")

    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role,
        "email": user.email,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return access_token, refresh_token, user.must_change_password, user


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    """Gera novos tokens a partir do refresh token."""
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise UnauthorizedError("Refresh token inválido ou expirado")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id), User.is_active))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("Usuário não encontrado")

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role,
        "email": user.email,
    }
    return create_access_token(token_data), create_refresh_token(token_data)


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: str,
    tenant_id: Optional[uuid.UUID] = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        tenant_id=tenant_id,
    )
    db.add(user)
    await db.flush()
    return user
