import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def check_sla_task():
    """Verifica violações de SLA em todos os tenants."""
    asyncio.run(_check_sla_async())


@celery_app.task
def send_boleto_reminders_task():
    """Envia lembretes de boleto vencendo nos próximos 3 dias via templates WhatsApp."""
    asyncio.run(_send_boleto_reminders_async())


async def _send_boleto_reminders_async():
    """
    Consulta boletos pendentes vencendo em até 3 dias e envia template de lembrete.
    Requer template 'boleto_lembrete' cadastrado no tenant.
    """
    from datetime import date, timedelta

    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.billing import Boleto
    from app.models.conversation import Contact
    from app.models.notification import MessageTemplate
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    hoje = date.today()
    limite = hoje + timedelta(days=3)

    async with AsyncSessionLocal() as db:
        # Busca boletos pendentes com vencimento em até 3 dias
        boletos_result = await db.execute(
            select(Boleto).where(
                Boleto.status == "pending",
                Boleto.due_date >= hoje,
                Boleto.due_date <= limite,
            )
        )
        boletos = boletos_result.scalars().all()

        if not boletos:
            logger.info("Nenhum boleto vencendo nos próximos 3 dias")
            return

        sent = 0
        for boleto in boletos:
            try:
                # Encontra contato do aluno
                from app.models.student import Student

                student_result = await db.execute(
                    select(Student).where(Student.id == boleto.student_id)
                )
                student = student_result.scalar_one_or_none()
                if not student:
                    continue

                contact_result = await db.execute(
                    select(Contact).where(
                        Contact.tenant_id == boleto.tenant_id,
                        Contact.student_id == student.id,
                        Contact.is_verified,
                    )
                )
                contact = contact_result.scalar_one_or_none()
                if not contact:
                    continue

                # Encontra template do tenant
                tmpl_result = await db.execute(
                    select(MessageTemplate).where(
                        MessageTemplate.tenant_id == boleto.tenant_id,
                        MessageTemplate.meta_template_name == "boleto_lembrete",
                        MessageTemplate.is_active,
                    )
                )
                template = tmpl_result.scalar_one_or_none()
                if not template:
                    continue

                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.id == boleto.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
                    continue

                await whatsapp_service.send_template_message(
                    phone_number_id=tenant.whatsapp_phone_number_id,
                    access_token=tenant.whatsapp_token,
                    to=contact.phone_number,
                    template_name="boleto_lembrete",
                    language_code=template.language_code,
                    components=[
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": student.full_name.split()[0]},
                                {"type": "text", "text": str(boleto.due_date.strftime("%d/%m/%Y"))},
                                {"type": "text", "text": f"R$ {boleto.amount:.2f}"},
                            ],
                        }
                    ],
                )
                sent += 1
            except Exception as exc:
                logger.error("Erro ao enviar lembrete para boleto %s: %s", boleto.id, exc)

        logger.info("Lembretes de boleto enviados: %d/%d", sent, len(boletos))


@celery_app.task
def send_attendance_alerts_task():
    """Alerta alunos com frequência abaixo de 75% em alguma disciplina."""
    asyncio.run(_send_attendance_alerts_async())


@celery_app.task
def send_grade_notifications_task():
    """Notifica alunos quando novas notas são lançadas."""
    asyncio.run(_send_grade_notifications_async())


async def _send_attendance_alerts_async():
    """Busca alunos com faltas acima de 25% e envia alerta via WhatsApp."""
    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.conversation import Contact
    from app.models.student import AttendanceRecord, Student
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    async with AsyncSessionLocal() as db:
        # Busca registros de frequência com ausência >= 25%
        records = await db.execute(
            select(AttendanceRecord).where(AttendanceRecord.absence_pct >= 25.0)
        )
        alerts = records.scalars().all()
        sent = 0

        for record in alerts:
            try:
                student_result = await db.execute(
                    select(Student).where(Student.id == record.student_id)
                )
                student = student_result.scalar_one_or_none()
                if not student:
                    continue

                contact_result = await db.execute(
                    select(Contact).where(
                        Contact.tenant_id == student.tenant_id,
                        Contact.student_id == student.id,
                        Contact.is_verified,
                    )
                )
                contact = contact_result.scalar_one_or_none()
                if not contact:
                    continue

                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.id == student.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
                    continue

                msg = (
                    f"Oi, {student.full_name.split()[0]}! "
                    f"Sua frequencia em *{record.subject_name}* esta em "
                    f"{100 - float(record.absence_pct):.0f}%. "
                    f"Fique atento para nao ultrapassar o limite de faltas!"
                )
                await whatsapp_service.send_text_message(
                    tenant.whatsapp_phone_number_id,
                    tenant.whatsapp_token,
                    contact.phone_number,
                    msg,
                )
                sent += 1
            except Exception as exc:
                logger.error("Erro ao enviar alerta frequencia: %s", exc)

        logger.info("Alertas de frequencia enviados: %d/%d", sent, len(alerts))


async def _send_grade_notifications_async():
    """Notifica alunos sobre notas recentemente lançadas (últimas 24h)."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.conversation import Contact
    from app.models.student import Grade, Student
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    async with AsyncSessionLocal() as db:
        grades = await db.execute(
            select(Grade).where(
                Grade.created_at >= since,
                Grade.grade_value.isnot(None),
            )
        )
        new_grades = grades.scalars().all()
        sent = 0

        for grade in new_grades:
            try:
                student_result = await db.execute(
                    select(Student).where(Student.id == grade.student_id)
                )
                student = student_result.scalar_one_or_none()
                if not student:
                    continue

                contact_result = await db.execute(
                    select(Contact).where(
                        Contact.tenant_id == student.tenant_id,
                        Contact.student_id == student.id,
                        Contact.is_verified,
                    )
                )
                contact = contact_result.scalar_one_or_none()
                if not contact:
                    continue

                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.id == student.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
                    continue

                msg = (
                    f"Oi, {student.full_name.split()[0]}! "
                    f"Uma nova nota foi lancada: *{grade.subject_name}* — "
                    f"{grade.grade_type}: *{grade.grade_value}*. "
                    f"Acesse o sistema para mais detalhes."
                )
                await whatsapp_service.send_text_message(
                    tenant.whatsapp_phone_number_id,
                    tenant.whatsapp_token,
                    contact.phone_number,
                    msg,
                )
                sent += 1
            except Exception as exc:
                logger.error("Erro ao notificar nota: %s", exc)

        logger.info("Notificacoes de notas enviadas: %d/%d", sent, len(new_grades))


async def _check_sla_async():
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.services.sla_service import check_sla_breaches

    async with AsyncSessionLocal() as db:
        breaches = await check_sla_breaches(db)
        if breaches:
            logger.warning("SLA violado em %d tickets", len(breaches))
            for b in breaches:
                logger.warning(
                    "SLA breach: tenant=%s ticket=%s priority=%s deadline=%s",
                    b["tenant_id"],
                    b["protocol"],
                    b["priority"],
                    b["deadline"],
                )
        await db.commit()
