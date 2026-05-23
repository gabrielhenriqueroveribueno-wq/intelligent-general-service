# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Tasks agendadas de health check dos providers de IA.

Roda periodicamente (ex: a cada 15 min), checa estado dos providers e:
- Loga um resumo no stdout (vai pro Loki)
- Se algum provider ficou critico (sem credito/auth), envia email pro admin
- Evita spam: so reenvia alerta se o estado mudou OU se ja passou 6h do ultimo
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from app.config import settings
from app.services import email_service, provider_health
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Estado em memoria do worker (simples — reseta no restart)
# ══════════════════════════════════════════════════════════════════════════════


ALERT_COOLDOWN_SECONDS = 6 * 3600  # 6 horas
_last_alert_fingerprint: Optional[str] = None
_last_alert_time: float = 0.0


def _alert_fingerprint(summary: dict) -> str:
    """Cria fingerprint unica do estado atual pra detectar mudancas."""
    parts = []
    for p in summary.get("providers", []):
        parts.append(f"{p['name']}:{p['state']}")
    return "|".join(sorted(parts))


def _should_send_alert(summary: dict) -> bool:
    global _last_alert_fingerprint, _last_alert_time

    fingerprint = _alert_fingerprint(summary)
    now = time.time()

    state_changed = fingerprint != _last_alert_fingerprint
    cooldown_passed = (now - _last_alert_time) > ALERT_COOLDOWN_SECONDS

    if state_changed or cooldown_passed:
        _last_alert_fingerprint = fingerprint
        _last_alert_time = now
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Email rendering
# ══════════════════════════════════════════════════════════════════════════════


def _render_alert_html(summary: dict) -> str:
    overall = summary.get("overall", "unknown")
    color = {
        "healthy": "#16a34a",
        "degraded": "#f59e0b",
        "critical": "#dc2626",
    }.get(overall, "#6b7280")

    rows = []
    for p in summary.get("providers", []):
        state = p.get("state", "?")
        detail = p.get("detail", "") or ""
        latency = p.get("latency_ms")
        latency_str = f"{latency}ms" if latency is not None else "-"
        circuit = "ABERTO" if p.get("circuit_open") else "fechado"

        state_color = "#16a34a" if state == "healthy" else "#dc2626"

        rows.append(
            f"<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #e5e7eb'><b>{p.get('name')}</b></td>"
            f"<td style='padding:8px;border-bottom:1px solid #e5e7eb;color:{state_color}'><b>{state}</b></td>"
            f"<td style='padding:8px;border-bottom:1px solid #e5e7eb'>{detail}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e5e7eb'>{latency_str}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e5e7eb'>{circuit}</td>"
            f"</tr>"
        )

    table = (
        "<table style='border-collapse:collapse;width:100%;font-family:sans-serif'>"
        "<thead><tr style='background:#f3f4f6'>"
        "<th style='padding:8px;text-align:left'>Provider</th>"
        "<th style='padding:8px;text-align:left'>Estado</th>"
        "<th style='padding:8px;text-align:left'>Detalhe</th>"
        "<th style='padding:8px;text-align:left'>Latencia</th>"
        "<th style='padding:8px;text-align:left'>Circuit</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )

    return f"""
    <div style='font-family:sans-serif;max-width:640px;margin:auto'>
      <h2 style='color:{color}'>IGS — Alerta de Saude dos Providers de IA</h2>
      <p>Estado geral: <b style='color:{color}'>{overall.upper()}</b></p>
      <p>{summary.get("healthy_count", 0)} de {summary.get("total_providers", 0)} providers saudaveis.</p>
      {table}
      <hr style='margin:24px 0;border:none;border-top:1px solid #e5e7eb'/>
      <p style='color:#6b7280;font-size:12px'>
        Verificado em {time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(summary.get("checked_at", time.time())))}.<br>
        Acesse o painel admin > IA Health para detalhes.
      </p>
    </div>
    """


def _render_alert_subject(summary: dict) -> str:
    overall = summary.get("overall", "unknown")
    if overall == "critical":
        return "[IGS][CRITICO] Todos os providers de IA estao fora do ar"
    if overall == "degraded":
        return "[IGS][AVISO] Providers de IA degradados"
    return "[IGS] Providers de IA saudaveis"


# ══════════════════════════════════════════════════════════════════════════════
# Celery tasks
# ══════════════════════════════════════════════════════════════════════════════


@celery_app.task(name="app.tasks.health_check_tasks.check_ai_providers_task")
def check_ai_providers_task():
    """
    Task agendada: verifica saude dos providers de IA e envia alerta se necessario.
    """
    asyncio.run(_check_ai_providers_async())


async def _check_ai_providers_async() -> None:
    try:
        statuses = await provider_health.check_all_providers()
    except Exception as exc:
        logger.exception("Falha ao executar health check dos providers: %s", exc)
        return

    summary = provider_health.summarize(statuses)
    overall = summary["overall"]

    logger.info(
        "AI health check: overall=%s, healthy=%d/%d",
        overall,
        summary["healthy_count"],
        summary["total_providers"],
    )

    for p in summary.get("providers", []):
        if p["state"] != "healthy":
            logger.warning(
                "Provider '%s' em estado '%s': %s",
                p["name"],
                p["state"],
                p.get("detail", ""),
            )

    if overall in ("critical", "degraded") and _should_send_alert(summary):
        to = settings.SUPER_ADMIN_EMAIL
        if not to:
            logger.warning("SUPER_ADMIN_EMAIL nao configurado — alerta nao enviado")
            return

        subject = _render_alert_subject(summary)
        body = _render_alert_html(summary)

        try:
            email_service.send_email(to=to, subject=subject, body=body)
            logger.info("Alerta de saude enviado para %s", to)
        except Exception as exc:
            logger.exception("Falha ao enviar alerta de saude: %s", exc)
