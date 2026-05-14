"""
Task de alerta de orçamento mensal de IA.

Roda diariamente às 8h. Soma os tokens de todos os tenants no mês corrente,
estima o custo em USD com preços aproximados por modelo e envia email
quando ultrapassar AI_BUDGET_ALERT_THRESHOLD (padrão 80%) do AI_MONTHLY_BUDGET_USD.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Preços aproximados por 1 000 tokens (input + output médio)
_COST_PER_1K: dict[str, float] = {
    "claude": 0.015,
    "groq": 0.0008,
    "gemini": 0.0005,
}

ALERT_COOLDOWN_SECONDS = 12 * 3600
_last_alert_sent_at: float = 0.0


def _estimate_cost(tokens: int, provider: str) -> float:
    rate = _COST_PER_1K.get(provider, 0.01)
    return (tokens / 1000.0) * rate


async def _run_budget_check() -> None:
    global _last_alert_sent_at
    import time

    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.models.conversation import Message
    from app.models.user import User

    engine = create_async_engine(settings.DATABASE_URL, pool_size=2, max_overflow=0)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as db:
        result = await db.execute(
            select(func.coalesce(func.sum(Message.ai_tokens_used), 0))
            .where(Message.created_at >= month_start)
        )
        total_tokens: int = result.scalar_one()

        # Fetch admin emails for notification
        admins = await db.execute(
            select(User.email).where(User.role.in_(["super_admin", "admin"]), User.is_active.is_(True))
        )
        admin_emails = [row[0] for row in admins.all()]

    await engine.dispose()

    provider = settings.AI_PROVIDER
    estimated_cost = _estimate_cost(total_tokens, provider)
    budget = settings.AI_MONTHLY_BUDGET_USD
    threshold = settings.AI_BUDGET_ALERT_THRESHOLD
    pct = estimated_cost / budget if budget > 0 else 0.0

    logger.info(
        "AI budget check: tokens=%d cost=US$%.2f budget=US$%.2f (%.0f%%)",
        total_tokens, estimated_cost, budget, pct * 100,
    )

    if pct < threshold:
        return

    now_ts = time.time()
    if now_ts - _last_alert_sent_at < ALERT_COOLDOWN_SECONDS:
        return

    _last_alert_sent_at = now_ts
    month_label = now.strftime("%B/%Y")

    subject = f"[IGS] Alerta de orçamento IA — {pct:.0%} do budget mensal atingido"
    body = f"""
<h2>Alerta de orçamento IA</h2>
<p>O uso de IA em <strong>{month_label}</strong> atingiu <strong>{pct:.0%}</strong>
do budget mensal configurado.</p>
<table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>Tokens usados no mês</td><td>{total_tokens:,}</td></tr>
  <tr><td>Custo estimado (USD)</td><td>US$ {estimated_cost:.2f}</td></tr>
  <tr><td>Budget mensal</td><td>US$ {budget:.2f}</td></tr>
  <tr><td>Provider</td><td>{provider}</td></tr>
</table>
<p style="margin-top:16px; font-size:13px; color:#6b7280;">
  Ajuste o orçamento em <code>AI_MONTHLY_BUDGET_USD</code> no .env
  ou o limiar em <code>AI_BUDGET_ALERT_THRESHOLD</code>.
</p>
"""
    from app.services.email_service import send_email_async
    from app.services.email_templates import _base

    for email in admin_emails[:5]:
        try:
            await send_email_async(to=email, subject=subject, body=_base("Alerta de orçamento IA", body))
        except Exception as exc:
            logger.warning("Falha ao enviar alerta de budget para %s: %s", email, exc)


@celery_app.task(name="app.tasks.ai_budget_tasks.check_ai_budget_task", bind=True, max_retries=2)
def check_ai_budget_task(self):
    try:
        asyncio.run(_run_budget_check())
    except Exception as exc:
        logger.exception("Erro no check de budget de IA: %s", exc)
        raise self.retry(exc=exc, countdown=300)
