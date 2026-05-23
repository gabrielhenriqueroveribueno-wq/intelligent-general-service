# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Historico de execucoes de sync por integracao.

Cada row = 1 execucao de run_integration_sync_task.
Permite visualizar tendencia de erros, volume, e performance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin


class SyncLog(Base, TenantMixin):
    __tablename__ = "integration_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success | error | partial

    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    employees_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    errors: Mapped[Optional[list]] = mapped_column(JSONB)
    warnings: Mapped[Optional[list]] = mapped_column(JSONB)
    error_summary: Mapped[Optional[str]] = mapped_column(Text)
