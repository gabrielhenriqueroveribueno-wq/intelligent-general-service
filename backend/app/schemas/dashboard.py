from typing import List

from pydantic import BaseModel


class MetricPoint(BaseModel):
    label: str
    value: float


class DashboardOverview(BaseModel):
    total_conversations_today: int
    total_conversations_week: int
    total_conversations_month: int
    auto_resolution_rate: float  # porcentagem
    avg_response_time_seconds: float
    open_tickets: int
    sla_breached_tickets: int
    active_agents: int
    avg_satisfaction_score: float = 0.0
    total_students: int = 0
    total_employees: int = 0
    total_messages_month: int = 0
    ai_tokens_month: int = 0
    estimated_cost_savings: float = 0.0


class DailyVolumePoint(BaseModel):
    date: str  # ISO (YYYY-MM-DD)
    label: str  # dia da semana abreviado pt-BR (seg, ter, ...)
    count: int


class IntentCount(BaseModel):
    intent: str
    count: int


class SentimentBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class CsatSummary(BaseModel):
    avg_score: float = 0.0  # 1-5
    responses: int = 0


class AiCostSummary(BaseModel):
    tokens_month: int = 0
    estimated_cost_usd: float = 0.0
    budget_usd: float = 0.0
    budget_used_pct: float = 0.0  # 0-100
    provider: str = "groq"


class DashboardInsights(BaseModel):
    """Dados ricos do dashboard: volume diario, demanda, sentimento, CSAT e custo de IA."""

    daily_volume: List[DailyVolumePoint] = []
    top_intents: List[IntentCount] = []
    sentiment: SentimentBreakdown = SentimentBreakdown()
    csat: CsatSummary = CsatSummary()
    ai_cost: AiCostSummary = AiCostSummary()


class SLAMetrics(BaseModel):
    total_tickets: int
    within_sla: int
    breached_sla: int
    compliance_rate: float
    by_priority: List[MetricPoint]


class VolumeMetrics(BaseModel):
    period: str
    points: List[MetricPoint]


class ResolutionMetrics(BaseModel):
    auto_resolved: int
    human_resolved: int
    pending: int
    auto_resolution_rate: float
