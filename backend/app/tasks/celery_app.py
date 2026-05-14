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
        "app.tasks.health_check_tasks",
        "app.tasks.executive_report_tasks",
        "app.tasks.integration_sync_tasks",
        "app.tasks.evasion_tasks",
        "app.tasks.push_tasks",
        "app.tasks.anonymization_tasks",
        "app.tasks.ai_budget_tasks",
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
        # Backup diário — todo dia às 3h
        "daily-db-backup": {
            "task": "app.tasks.backup_tasks.backup_database_task",
            "schedule": crontab(hour=3, minute=0),
        },
        # Relatório semanal para gestores via WhatsApp — toda segunda-feira às 8h
        "weekly-manager-report": {
            "task": "app.tasks.notification_tasks.send_weekly_report_task",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),
        },
        # Relatório PDF semanal por email — toda segunda-feira às 8:30h
        "weekly-pdf-report": {
            "task": "app.tasks.notification_tasks.send_weekly_pdf_report_task",
            "schedule": crontab(hour=8, minute=30, day_of_week=1),
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
        # Health check dos providers de IA — a cada 15 minutos
        "ai-providers-health-check": {
            "task": "app.tasks.health_check_tasks.check_ai_providers_task",
            "schedule": crontab(minute="*/15"),
        },
        # Despacha relatorios executivos por email — de hora em hora
        "dispatch-scheduled-reports": {
            "task": "app.tasks.executive_report_tasks.dispatch_scheduled_reports_task",
            "schedule": crontab(minute=5),  # minuto 5 de cada hora
        },
        # Despacha syncs de sistemas academicos — de hora em hora
        "dispatch-integration-syncs": {
            "task": "app.tasks.integration_sync_tasks.dispatch_integration_syncs_task",
            "schedule": crontab(minute=15),  # minuto 15 de cada hora
        },
        # Calcula risco de evasão — a cada hora
        "compute-evasion-risks": {
            "task": "app.tasks.evasion_tasks.compute_evasion_risks_task",
            "schedule": crontab(minute=45),  # minuto 45 de cada hora
        },
        # Anonimização LGPD automática — todo dia 1° às 2h
        "auto-anonymize-lgpd": {
            "task": "app.tasks.anonymization_tasks.auto_anonymize_task",
            "schedule": crontab(hour=2, minute=0, day_of_month=1),
        },
        # Alerta de budget mensal de IA — todo dia às 8h
        "ai-budget-check": {
            "task": "app.tasks.ai_budget_tasks.check_ai_budget_task",
            "schedule": crontab(hour=8, minute=0),
        },
    },
)
