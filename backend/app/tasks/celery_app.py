from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "igs",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.message_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Verifica SLA a cada 5 minutos
        "check-sla-breaches": {
            "task": "app.tasks.notification_tasks.check_sla_task",
            "schedule": crontab(minute="*/5"),
        },
    },
)
