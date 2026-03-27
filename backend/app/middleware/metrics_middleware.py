from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Métricas customizadas IGS
messages_processed_total = Counter(
    "igs_messages_processed_total",
    "Total de mensagens WhatsApp processadas",
    ["tenant_id", "intent", "resolution_type"],
)

ai_tokens_used_total = Counter(
    "igs_ai_tokens_used_total",
    "Total de tokens Claude consumidos",
    ["tenant_id", "call_type"],
)

sla_breaches_total = Counter(
    "igs_sla_breaches_total",
    "Total de violações de SLA",
    ["tenant_id", "priority"],
)

active_conversations = Gauge(
    "igs_active_conversations",
    "Conversas ativas no momento",
    ["tenant_id"],
)

response_time_histogram = Histogram(
    "igs_bot_response_time_seconds",
    "Tempo de resposta do bot em segundos",
    ["tenant_id"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)


def setup_metrics(app: FastAPI) -> None:
    """Configura o Prometheus na aplicação FastAPI."""
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health", "/nginx-health"],
    ).instrument(app).expose(app, endpoint="/metrics")
