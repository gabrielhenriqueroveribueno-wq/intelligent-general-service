"""
Servico de relatorios executivos por email.

Gera resumos com KPIs ricos pra gestores nao-tecnicos:
- Metricas do periodo (conversas, resolucao automatica, tempo de resposta, satisfacao)
- Comparacao com periodo anterior (% variacao)
- Top intents
- Tickets pendentes / SLA violado
- HTML formatado pra leitura no proprio email (sem precisar abrir anexo)

Suporta tres periodos:
- daily: ultimas 24h
- weekly: ultimos 7 dias
- monthly: ultimos 30 dias
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.satisfaction import SatisfactionSurvey
from app.models.ticket import Ticket

logger = logging.getLogger(__name__)


Period = Literal["daily", "weekly", "monthly"]

PERIOD_LABEL = {
    "daily": "Diario",
    "weekly": "Semanal",
    "monthly": "Mensal",
}

PERIOD_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}


# ══════════════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class TrendValue:
    current: float
    previous: float
    delta_pct: Optional[float] = None  # variacao % vs periodo anterior

    def __post_init__(self):
        if self.previous == 0 and self.current == 0:
            self.delta_pct = 0.0
        elif self.previous == 0:
            self.delta_pct = None  # nao da pra calcular % de zero
        else:
            self.delta_pct = ((self.current - self.previous) / self.previous) * 100


@dataclass
class IntentCount:
    intent: str
    count: int


@dataclass
class ExecutiveReportData:
    tenant_id: uuid.UUID
    tenant_name: str
    period: Period
    start_date: datetime
    end_date: datetime
    total_conversations: TrendValue = field(default_factory=lambda: TrendValue(0, 0))
    bot_resolutions: TrendValue = field(default_factory=lambda: TrendValue(0, 0))
    avg_satisfaction: Optional[float] = None
    auto_resolution_rate: float = 0.0
    open_tickets: int = 0
    sla_breached: int = 0
    top_intents: list[IntentCount] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Data aggregation
# ══════════════════════════════════════════════════════════════════════════════


async def _count_conversations(
    db: AsyncSession, tenant_id: uuid.UUID, start: datetime, end: datetime
) -> int:
    result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= start,
            Conversation.started_at < end,
        )
    )
    return result.scalar() or 0


async def _count_bot_resolutions(
    db: AsyncSession, tenant_id: uuid.UUID, start: datetime, end: datetime
) -> int:
    """Conversas fechadas no periodo que nao geraram ticket (resolvidas pela IA)."""
    result = await db.execute(
        select(func.count(Conversation.id))
        .outerjoin(Ticket, Ticket.conversation_id == Conversation.id)
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.started_at >= start,
            Conversation.started_at < end,
            Conversation.status == "closed",
            Ticket.id.is_(None),
        )
    )
    return result.scalar() or 0


async def _avg_satisfaction(
    db: AsyncSession, tenant_id: uuid.UUID, start: datetime, end: datetime
) -> Optional[float]:
    result = await db.execute(
        select(func.avg(SatisfactionSurvey.score)).where(
            SatisfactionSurvey.tenant_id == tenant_id,
            SatisfactionSurvey.responded_at >= start,
            SatisfactionSurvey.responded_at < end,
        )
    )
    val = result.scalar()
    return float(val) if val is not None else None


async def _count_open_tickets(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == tenant_id,
            Ticket.status.in_(["open", "in_progress"]),
        )
    )
    return result.scalar() or 0


async def _count_sla_breached(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == tenant_id,
            Ticket.status.in_(["open", "in_progress"]),
            Ticket.sla_deadline.isnot(None),
            Ticket.sla_deadline < now,
        )
    )
    return result.scalar() or 0


async def _top_intents(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start: datetime,
    end: datetime,
    limit: int = 5,
) -> list[IntentCount]:
    result = await db.execute(
        select(Message.intent, func.count(Message.id).label("c"))
        .where(
            Message.tenant_id == tenant_id,
            Message.created_at >= start,
            Message.created_at < end,
            Message.intent.isnot(None),
            Message.sender_type == "user",
        )
        .group_by(Message.intent)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
    )
    return [IntentCount(intent=row[0] or "outros", count=row[1]) for row in result.all()]


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════


async def build_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    tenant_name: str,
    period: Period = "weekly",
    end: Optional[datetime] = None,
) -> ExecutiveReportData:
    """Constroi um snapshot de KPIs do periodo, comparando com o anterior."""
    end = end or datetime.now(timezone.utc)
    days = PERIOD_DAYS[period]
    start = end - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    total_curr = await _count_conversations(db, tenant_id, start, end)
    total_prev = await _count_conversations(db, tenant_id, prev_start, start)

    bot_curr = await _count_bot_resolutions(db, tenant_id, start, end)
    bot_prev = await _count_bot_resolutions(db, tenant_id, prev_start, start)

    auto_rate = (bot_curr / total_curr * 100) if total_curr > 0 else 0.0

    return ExecutiveReportData(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        period=period,
        start_date=start,
        end_date=end,
        total_conversations=TrendValue(current=total_curr, previous=total_prev),
        bot_resolutions=TrendValue(current=bot_curr, previous=bot_prev),
        avg_satisfaction=await _avg_satisfaction(db, tenant_id, start, end),
        auto_resolution_rate=auto_rate,
        open_tickets=await _count_open_tickets(db, tenant_id),
        sla_breached=await _count_sla_breached(db, tenant_id),
        top_intents=await _top_intents(db, tenant_id, start, end),
    )


# ══════════════════════════════════════════════════════════════════════════════
# HTML rendering
# ══════════════════════════════════════════════════════════════════════════════


INTENT_LABELS = {
    "grade_query": "Consulta de notas",
    "attendance_query": "Frequencia / faltas",
    "boleto_query": "Boletos / pagamento",
    "schedule_query": "Horarios / grade",
    "payslip_query": "Holerite",
    "vacation_query": "Ferias",
    "handoff": "Transferencia humano",
    "general_query": "Geral",
    "document_query": "Documentos",
    "schedule_appointment": "Agendamento",
    "feedback_response": "Resposta de feedback",
    "farewell": "Despedida",
    "greeting": "Saudacao",
    "outros": "Outros",
}


def _arrow(delta: Optional[float]) -> str:
    if delta is None:
        return "—"
    if delta > 5:
        return f'<span style="color:#16a34a;font-weight:600">▲ {delta:+.1f}%</span>'
    if delta < -5:
        return f'<span style="color:#dc2626;font-weight:600">▼ {delta:+.1f}%</span>'
    return f'<span style="color:#6b7280">▬ {delta:+.1f}%</span>'


def render_report_html(data: ExecutiveReportData) -> str:
    period_label = PERIOD_LABEL[data.period]
    period_str = (
        f"{data.start_date.strftime('%d/%m/%Y')} a {data.end_date.strftime('%d/%m/%Y')}"
    )
    sat_str = f"{data.avg_satisfaction:.1f}/5" if data.avg_satisfaction is not None else "—"

    intents_rows = "".join(
        f"<tr>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb'>{INTENT_LABELS.get(i.intent, i.intent)}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600'>{i.count}</td>"
        f"</tr>"
        for i in data.top_intents
    )
    if not intents_rows:
        intents_rows = (
            "<tr><td colspan='2' style='padding:12px;text-align:center;color:#9ca3af'>"
            "Sem dados de intent no periodo</td></tr>"
        )

    sla_alert = ""
    if data.sla_breached > 0:
        sla_alert = (
            f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;'
            f'padding:12px;margin:16px 0">'
            f'<strong style="color:#dc2626">⚠️ Atencao:</strong> '
            f'<span style="color:#7f1d1d">{data.sla_breached} ticket(s) com SLA violado</span>'
            f'</div>'
        )

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:640px;margin:0 auto;color:#111827">
      <div style="background:linear-gradient(135deg,#1d4ed8 0%,#312e81 100%);padding:32px 24px;border-radius:12px 12px 0 0;color:white">
        <p style="margin:0;font-size:12px;opacity:0.8;letter-spacing:1px;text-transform:uppercase">
          IGS — Relatorio {period_label}
        </p>
        <h1 style="margin:8px 0 4px;font-size:24px">{data.tenant_name}</h1>
        <p style="margin:0;opacity:0.9;font-size:14px">{period_str}</p>
      </div>

      <div style="background:white;padding:24px;border:1px solid #e5e7eb;border-top:0">
        <h2 style="margin:0 0 16px;font-size:18px;color:#111827">📊 KPIs do periodo</h2>

        <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
          <tr>
            <td style="padding:16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;width:48%">
              <p style="margin:0;font-size:12px;color:#6b7280">Conversas</p>
              <p style="margin:4px 0;font-size:28px;font-weight:700;color:#1d4ed8">{int(data.total_conversations.current)}</p>
              <p style="margin:0;font-size:12px">{_arrow(data.total_conversations.delta_pct)} vs periodo anterior</p>
            </td>
            <td style="width:4%"></td>
            <td style="padding:16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;width:48%">
              <p style="margin:0;font-size:12px;color:#6b7280">Resolucao automatica</p>
              <p style="margin:4px 0;font-size:28px;font-weight:700;color:#16a34a">{data.auto_resolution_rate:.1f}%</p>
              <p style="margin:0;font-size:12px;color:#6b7280">{int(data.bot_resolutions.current)} de {int(data.total_conversations.current)} pelo bot</p>
            </td>
          </tr>
          <tr><td style="height:12px"></td></tr>
          <tr>
            <td style="padding:16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px">
              <p style="margin:0;font-size:12px;color:#6b7280">Satisfacao media</p>
              <p style="margin:4px 0;font-size:28px;font-weight:700;color:#f59e0b">{sat_str}</p>
              <p style="margin:0;font-size:12px;color:#6b7280">avaliacao dos alunos</p>
            </td>
            <td></td>
            <td style="padding:16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px">
              <p style="margin:0;font-size:12px;color:#6b7280">Tickets abertos</p>
              <p style="margin:4px 0;font-size:28px;font-weight:700;color:#7c3aed">{data.open_tickets}</p>
              <p style="margin:0;font-size:12px;color:#dc2626">{data.sla_breached} com SLA violado</p>
            </td>
          </tr>
        </table>

        {sla_alert}

        <h3 style="margin:24px 0 12px;font-size:16px;color:#111827">🎯 Top assuntos</h3>
        <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
          <thead>
            <tr style="background:#f3f4f6">
              <th style="padding:8px 12px;text-align:left;font-size:13px">Assunto</th>
              <th style="padding:8px 12px;text-align:right;font-size:13px">Mensagens</th>
            </tr>
          </thead>
          <tbody>
            {intents_rows}
          </tbody>
        </table>
      </div>

      <div style="background:#f9fafb;padding:16px 24px;border:1px solid #e5e7eb;border-top:0;border-radius:0 0 12px 12px;text-align:center">
        <p style="margin:0;font-size:12px;color:#6b7280">
          Acesse o painel completo em <a href="https://igs.com.br/app/dashboard" style="color:#1d4ed8">igs.com.br/app/dashboard</a>
        </p>
        <p style="margin:8px 0 0;font-size:11px;color:#9ca3af">
          Voce esta recebendo este email porque eh administrador do tenant {data.tenant_name}.
          Para deixar de receber, ajuste em Configuracoes > Relatorios.
        </p>
      </div>
    </div>
    """


def render_subject(data: ExecutiveReportData) -> str:
    period_label = PERIOD_LABEL[data.period]
    return f"[IGS] Relatorio {period_label} - {data.tenant_name} ({int(data.total_conversations.current)} conversas)"
