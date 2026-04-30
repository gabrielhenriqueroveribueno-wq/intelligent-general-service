"""
Modelo de configuracao de integracao com sistemas academicos externos.

Cada tenant pode ter UMA integracao ativa por vez (Sophia, TOTVS, REST generico).
As credenciais ficam criptografadas via Fernet.

Status:
- active   → sincroniza periodicamente
- paused   → existe mas nao sincroniza (usuario desativou)
- error    → ultima sync falhou; precisa intervencao
- pending  → recem-criada, ainda nao sincronizou
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin


class AcademicIntegration(Base, TenantMixin, TimestampMixin):
    """Configuracao da integracao do tenant com sistema academico."""

    __tablename__ = "academic_integrations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_type", name="uq_integration_tenant_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tipo: 'sophia', 'totvs', 'generic_rest'
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Nome amigavel (ex: "Sophia Producao")
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Configuracao publica (URLs, IDs, mappings) — JSON
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Credenciais sensiveis (api_key, password, token) — Fernet-encrypted JSON
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text)

    # Estado
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Sync schedule (cron expression) — default a cada 6h
    sync_cron: Mapped[str] = mapped_column(String(50), nullable=False, default="0 */6 * * *")

    # Estatisticas da ultima sync
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_sync_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    last_sync_records_synced: Mapped[Optional[int]] = mapped_column(Integer)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text)
