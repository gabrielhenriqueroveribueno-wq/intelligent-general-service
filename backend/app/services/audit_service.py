# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Audit log helper — registra ações sensíveis em audit_logs.

Uso típico (dentro de endpoint/serviço com sessão ativa):

    from app.services.audit_service import log_event, extract_ip

    await log_event(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="login_success",
        ip=extract_ip(request),
    )

O helper apenas adiciona o registro à sessão atual — o caller decide quando
fazer commit. Isso garante atomicidade com a ação sendo auditada.

Boas práticas:
- Use ações em snake_case curtas e estáveis (login_success, password_changed)
- Não coloque PII em `details` (apenas IDs, contadores, motivos)
- O modelo é imutável por convenção: nunca atualize/delete linhas de audit_logs
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


# Ações canônicas — manter em snake_case e estáveis.
# Quem ler audit logs depois espera esses valores exatos.
ACTION_LOGIN_SUCCESS = "login_success"
ACTION_LOGIN_FAILED = "login_failed"
ACTION_PASSWORD_CHANGED = "password_changed"
ACTION_PASSWORD_RESET_REQUESTED = "password_reset_requested"
ACTION_PASSWORD_RESET_COMPLETED = "password_reset_completed"
ACTION_ACCOUNT_DELETED = "account_deleted"
ACTION_DATA_EXPORTED = "data_exported"
ACTION_TENANT_CREATED = "tenant_created"
ACTION_TENANT_UPDATED = "tenant_updated"
ACTION_USER_CREATED = "user_created"
ACTION_USER_ROLE_CHANGED = "user_role_changed"


async def log_event(
    db: AsyncSession,
    *,
    action: str,
    tenant_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    details: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """Registra um evento de auditoria na sessão do caller.

    Não faz commit — o caller controla a transação. Isso garante que
    o audit log fica atômico com a ação auditada (tudo-ou-nada).
    Útil para eventos de sucesso (login_success, password_changed)
    onde queremos que o log seja revertido se a operação principal falhar.

    Em caso de erro ao construir/adicionar, apenas loga e segue —
    audit nunca deve quebrar fluxo do usuário.
    """
    try:
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip,
        )
        db.add(audit)
    except Exception as exc:
        logger.warning("Falha ao registrar audit log (action=%s): %s", action, exc)


async def log_event_isolated(
    *,
    action: str,
    tenant_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    details: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """Registra um evento de auditoria em uma transação isolada.

    Abre sessão própria e commita imediatamente. Use quando o evento
    precisa ser persistido independentemente do fluxo principal —
    ex: login_failed (a request termina em exception/rollback, mas o
    log de falha precisa sobreviver para forensics).

    Fail-safe: nunca propaga exception ao caller. Se o DB cair, só loga.
    """
    try:
        # Import local para evitar ciclo (dependencies importa este módulo
        # indiretamente via services).
        from app.dependencies import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details or {},
                ip_address=ip,
            )
            session.add(audit)
            await session.commit()
    except Exception as exc:
        logger.warning("Falha ao registrar audit log isolado (action=%s): %s", action, exc)


def extract_ip(request: Optional[Request]) -> Optional[str]:
    """Extrai IP do cliente respeitando X-Forwarded-For (atrás de proxy/Caddy)."""
    if request is None:
        return None
    # X-Forwarded-For pode ter múltiplos IPs separados por vírgula —
    # o primeiro é o cliente original.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    return None
