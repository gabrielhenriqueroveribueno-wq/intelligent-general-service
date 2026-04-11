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
        "app.tasks.dlq_tasks",
        "app.tasks.backup_tasks",
        "app.tasks.webhook_tasks",
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
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Verifica SLA a cada 5 minutos
        "check-sla-breaches": {
            "task": "app.tasks.notification_tasks.check_sla_task",
            "schedule": crontab(minute="*/5"),
        },
        # Lembretes de boleto vencendo — todo dia às 9h
        "send-boleto-reminders": {
            "task": "app.tasks.notification_tasks.send_boleto_reminders_task",
            "schedule": crontab(hour=9, minute=0),
        },
        # Alertas de frequência — todo dia às 10h
        "send-attendance-alerts": {
            "task": "app.tasks.notification_tasks.send_attendance_alerts_task",
            "schedule": crontab(hour=10, minute=0),
        },
        # Notificações de notas — a cada 6 horas
        "send-grade-notifications": {
            "task": "app.tasks.notification_tasks.send_grade_notifications_task",
            "schedule": crontab(hour="*/6", minute=30),
        },
        # Backup semanal do banco — toda segunda-feira às 3h
        "weekly-db-backup": {
            "task": "app.tasks.backup_tasks.backup_database_task",
            "schedule": crontab(hour=3, minute=0, day_of_week=1),
        },
        # Relatório semanal para gestores — toda segunda-feira às 8h
        "weekly-manager-report": {
            "task": "app.tasks.notification_tasks.send_weekly_report_task",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),
        },
        # Alerta de risco de evasão — todo dia às 7h
        "check-evasion-risk": {
            "task": "app.tasks.notification_tasks.check_evasion_risk_task",
            "schedule": crontab(hour=7, minute=0),
        },
        # Campanha de rematrícula — todo dia às 9h (só roda em jun/jul/nov/dez)
        "reenrollment-campaign": {
            "task": "app.tasks.notification_tasks.send_reenrollment_campaign_task",
            "schedule": crontab(hour=9, minute=30),
        },
    },
)
