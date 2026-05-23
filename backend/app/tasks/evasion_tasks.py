# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Tarefa periódica de análise de risco de evasão.
Roda a cada hora via celery beat e atualiza evasion_risk_score/level em todos os alunos ativos.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def compute_evasion_risks_task() -> None:
    """Calcula risco de evasão para todos os alunos ativos de todos os tenants."""
    asyncio.run(_run())


async def _run() -> None:
    from sqlalchemy import select, update

    from app.dependencies import WorkerSessionLocal
    from app.models.student import Student
    from app.models.tenant import Tenant
    from app.services.evasion_service import compute_all_risks

    async with WorkerSessionLocal() as db:
        tenants_res = await db.execute(select(Tenant.id).where(Tenant.is_active == True))  # noqa: E712
        tenant_ids = tenants_res.scalars().all()

        total_updated = 0
        for tid in tenant_ids:
            try:
                risks = await compute_all_risks(db, tid)
                for risk in risks:
                    await db.execute(
                        update(Student)
                        .where(Student.id == risk.student_id)
                        .values(
                            evasion_risk_score=risk.score,
                            evasion_risk_level=risk.level,
                            evasion_risk_updated_at=datetime.now(timezone.utc),
                            evasion_factors=json.dumps(risk.factors, ensure_ascii=False),
                        )
                    )
                    total_updated += 1
                await db.commit()
                logger.info("Evasão: tenant=%s updated=%d", tid, len(risks))
            except Exception as exc:
                logger.error("Erro ao calcular evasão tenant=%s: %s", tid, exc)
                await db.rollback()

        logger.info("Evasão concluída: %d alunos atualizados", total_updated)
