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
