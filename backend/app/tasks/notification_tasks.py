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

                # Verifica opt-in de lembretes
                contact_meta = contact.metadata_ or {}
                if not contact_meta.get("reminders_enabled", False):
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

                # Verifica opt-in de lembretes
                contact_meta = contact.metadata_ or {}
                if not contact_meta.get("reminders_enabled", False):
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

                # Verifica opt-in de lembretes
                contact_meta = contact.metadata_ or {}
                if not contact_meta.get("reminders_enabled", False):
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


@celery_app.task
def send_weekly_pdf_report_task():
    """Gera relatório PDF semanal e envia por email para gestores."""
    asyncio.run(_send_weekly_pdf_report_async())


@celery_app.task
def send_weekly_report_task():
    """Envia relatório semanal de atendimento para gestores do tenant."""
    asyncio.run(_send_weekly_report_async())


@celery_app.task
def check_evasion_risk_task():
    """Verifica alunos com risco de evasão e alerta coordenação."""
    asyncio.run(_check_evasion_risk_async())


@celery_app.task
def send_reenrollment_campaign_task():
    """Envia campanha de rematrícula para alunos com matrícula vencendo."""
    asyncio.run(_send_reenrollment_campaign_async())


@celery_app.task
def generate_document_task(contact_id: str, tenant_id: str, doc_type: str):
    """Gera documento (declaração, histórico) e envia via WhatsApp."""
    asyncio.run(_generate_document_async(contact_id, tenant_id, doc_type))


async def _send_weekly_report_async():
    """Agrega métricas da semana e envia resumo para admins do tenant."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func, select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.conversation import Contact, Conversation, Message
    from app.models.satisfaction import SatisfactionSurvey
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services import whatsapp_service

    since = datetime.now(timezone.utc) - timedelta(days=7)

    async with AsyncSessionLocal() as db:
        tenants = await db.execute(select(Tenant).where(Tenant.is_active))
        for tenant in tenants.scalars().all():
            try:
                # Total de mensagens na semana
                msg_count = await db.execute(
                    select(func.count(Message.id)).where(
                        Message.tenant_id == tenant.id,
                        Message.created_at >= since,
                        Message.sender_type == "user",
                    )
                )
                total_msgs = msg_count.scalar() or 0

                # Total de conversas
                conv_count = await db.execute(
                    select(func.count(Conversation.id)).where(
                        Conversation.tenant_id == tenant.id,
                        Conversation.created_at >= since,
                    )
                )
                total_convs = conv_count.scalar() or 0

                # Intents mais frequentes
                top_intents = await db.execute(
                    select(Message.intent, func.count(Message.id).label("cnt"))
                    .where(
                        Message.tenant_id == tenant.id,
                        Message.created_at >= since,
                        Message.intent.isnot(None),
                        Message.intent != "greeting",
                        Message.intent != "unknown",
                    )
                    .group_by(Message.intent)
                    .order_by(func.count(Message.id).desc())
                    .limit(5)
                )
                intents_list = top_intents.all()

                # Média de satisfação
                avg_score = await db.execute(
                    select(func.avg(SatisfactionSurvey.score)).where(
                        SatisfactionSurvey.tenant_id == tenant.id,
                        SatisfactionSurvey.created_at >= since,
                        SatisfactionSurvey.score.isnot(None),
                    )
                )
                satisfaction = avg_score.scalar()

                # Monta relatório
                intent_lines = (
                    "\n".join(f"  - {name}: {cnt}x" for name, cnt in intents_list)
                    or "  - Sem dados"
                )

                sat_text = f"{satisfaction:.1f}/5" if satisfaction else "Sem avaliações"

                report = (
                    f"*Relatório Semanal — IGS*\n\n"
                    f"- Mensagens recebidas: *{total_msgs}*\n"
                    f"- Conversas abertas: *{total_convs}*\n"
                    f"- Satisfação média: *{sat_text}*\n\n"
                    f"*Top assuntos:*\n{intent_lines}"
                )

                # Envia para admins/managers do tenant
                admins = await db.execute(
                    select(User).where(
                        User.tenant_id == tenant.id,
                        User.role.in_(["admin", "manager"]),
                        User.is_active,
                    )
                )
                for admin in admins.scalars().all():
                    # Busca contato do admin pelo telefone
                    admin_contact = await db.execute(
                        select(Contact).where(
                            Contact.tenant_id == tenant.id,
                            Contact.name == admin.full_name,
                        )
                    )
                    contact = admin_contact.scalar_one_or_none()
                    if contact and tenant.whatsapp_phone_number_id and tenant.whatsapp_token:
                        await whatsapp_service.send_text_message(
                            tenant.whatsapp_phone_number_id,
                            tenant.whatsapp_token,
                            contact.phone_number,
                            report,
                        )

                logger.info("Relatório semanal enviado para tenant %s", tenant.slug)
            except Exception as exc:
                logger.error("Erro no relatório semanal tenant %s: %s", tenant.id, exc)


async def _check_evasion_risk_async():
    """Cruza faltas + notas + boletos para identificar risco de evasão."""
    from sqlalchemy import func, select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.billing import Boleto
    from app.models.conversation import Contact
    from app.models.student import AttendanceRecord, Grade, Student
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    async with AsyncSessionLocal() as db:
        tenants = await db.execute(select(Tenant).where(Tenant.is_active))
        for tenant in tenants.scalars().all():
            try:
                students = await db.execute(
                    select(Student).where(
                        Student.tenant_id == tenant.id,
                        Student.enrollment_status == "active",
                    )
                )
                for student in students.scalars().all():
                    risk_signals = []

                    # Sinal 1: frequência abaixo de 70% em alguma matéria
                    attendance = await db.execute(
                        select(AttendanceRecord).where(
                            AttendanceRecord.student_id == student.id,
                            AttendanceRecord.absence_pct >= 30.0,
                        )
                    )
                    low_attendance = attendance.scalars().all()
                    if low_attendance:
                        risk_signals.append(
                            f"Frequência crítica em {len(low_attendance)} disciplina(s)"
                        )

                    # Sinal 2: nota abaixo de 4.0
                    grades = await db.execute(
                        select(Grade).where(
                            Grade.student_id == student.id,
                            Grade.grade_value < 4.0,
                            Grade.grade_value.isnot(None),
                        )
                    )
                    low_grades = grades.scalars().all()
                    if low_grades:
                        risk_signals.append(
                            f"Notas abaixo de 4.0 em {len(low_grades)} avaliação(ões)"
                        )

                    # Sinal 3: boletos vencidos
                    overdue = await db.execute(
                        select(func.count(Boleto.id)).where(
                            Boleto.student_id == student.id,
                            Boleto.status == "overdue",
                        )
                    )
                    overdue_count = overdue.scalar() or 0
                    if overdue_count > 0:
                        risk_signals.append(f"{overdue_count} boleto(s) vencido(s)")

                    # Alerta se 2+ sinais
                    if len(risk_signals) >= 2:
                        if not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
                            continue

                        alert = (
                            f"*Alerta de Risco de Evasão*\n\n"
                            f"Aluno: *{student.full_name}*\n"
                            f"RA: *{student.registration_number}*\n"
                            f"Curso: *{student.course}*\n\n"
                            f"Sinais identificados:\n" + "\n".join(f"  - {s}" for s in risk_signals)
                        )

                        # Envia para admins do tenant
                        from app.models.user import User

                        admins = await db.execute(
                            select(User).where(
                                User.tenant_id == tenant.id,
                                User.role.in_(["admin", "manager"]),
                                User.is_active,
                            )
                        )
                        for admin in admins.scalars().all():
                            admin_contact = await db.execute(
                                select(Contact).where(
                                    Contact.tenant_id == tenant.id,
                                    Contact.name == admin.full_name,
                                )
                            )
                            contact = admin_contact.scalar_one_or_none()
                            if contact:
                                await whatsapp_service.send_text_message(
                                    tenant.whatsapp_phone_number_id,
                                    tenant.whatsapp_token,
                                    contact.phone_number,
                                    alert,
                                )

                        logger.info(
                            "Alerta evasão: %s (%d sinais)",
                            student.full_name,
                            len(risk_signals),
                        )
            except Exception as exc:
                logger.error("Erro check evasão tenant %s: %s", tenant.id, exc)


async def _send_reenrollment_campaign_async():
    """Envia mensagem de rematrícula para alunos com matrícula ativa."""
    from datetime import date

    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.conversation import Contact
    from app.models.student import Student
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    today = date.today()
    # Campanha roda em junho (2026.2) e dezembro (2027.1)
    if today.month not in (6, 7, 11, 12):
        logger.info("Fora do período de rematrícula, pulando campanha")
        return

    async with AsyncSessionLocal() as db:
        tenants = await db.execute(select(Tenant).where(Tenant.is_active))
        for tenant in tenants.scalars().all():
            if not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
                continue

            try:
                students = await db.execute(
                    select(Student).where(
                        Student.tenant_id == tenant.id,
                        Student.enrollment_status == "active",
                    )
                )
                sent = 0
                for student in students.scalars().all():
                    contact_result = await db.execute(
                        select(Contact).where(
                            Contact.tenant_id == tenant.id,
                            Contact.student_id == student.id,
                            Contact.is_verified,
                        )
                    )
                    contact = contact_result.scalar_one_or_none()
                    if not contact:
                        continue

                    # Verifica opt-in
                    contact_meta = contact.metadata_ or {}
                    if not contact_meta.get("reminders_enabled", False):
                        continue

                    first_name = student.full_name.split()[0]
                    msg = (
                        f"Oi, {first_name}! O período de *rematrícula* já abriu. "
                        f"Quer que eu te ajude com o processo? É só me chamar aqui 😊"
                    )
                    await whatsapp_service.send_text_message(
                        tenant.whatsapp_phone_number_id,
                        tenant.whatsapp_token,
                        contact.phone_number,
                        msg,
                    )
                    sent += 1

                logger.info("Campanha rematrícula tenant %s: %d enviados", tenant.slug, sent)
            except Exception as exc:
                logger.error("Erro campanha rematrícula tenant %s: %s", tenant.id, exc)


async def _generate_document_async(contact_id: str, tenant_id: str, doc_type: str):
    """Gera documento e envia como mensagem WhatsApp."""
    import uuid as _uuid

    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.conversation import Contact
    from app.models.student import Student
    from app.models.tenant import Tenant
    from app.services import whatsapp_service

    async with AsyncSessionLocal() as db:
        contact = await db.execute(select(Contact).where(Contact.id == _uuid.UUID(contact_id)))
        contact = contact.scalar_one_or_none()
        if not contact or not contact.student_id:
            return

        student = await db.execute(select(Student).where(Student.id == contact.student_id))
        student = student.scalar_one_or_none()
        if not student:
            return

        tenant = await db.execute(select(Tenant).where(Tenant.id == _uuid.UUID(tenant_id)))
        tenant = tenant.scalar_one_or_none()
        if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
            return

        from datetime import date

        today = date.today().strftime("%d/%m/%Y")

        if doc_type == "enrollment_declaration":
            doc_text = (
                f"*DECLARAÇÃO DE MATRÍCULA*\n\n"
                f"Declaramos que *{student.full_name}*, "
                f"RA *{student.registration_number}*, "
                f"encontra-se regularmente matriculado(a) no curso de "
                f"*{student.course or 'N/I'}*, "
                f"*{student.semester}º semestre*, "
                f"nesta instituição de ensino.\n\n"
                f"Status: *{student.enrollment_status}*\n"
                f"Data de emissão: *{today}*\n\n"
                f"_Documento gerado digitalmente pelo sistema IGS._\n"
                f"_Para validação, entre em contato com a secretaria._"
            )
        elif doc_type == "academic_history":
            from app.services import student_service

            grades = await student_service.get_grades(db, _uuid.UUID(tenant_id), student.id)
            grade_lines = (
                "\n".join(
                    f"- *{g.subject_name}* ({g.academic_period}) — "
                    f"{g.grade_type}: *{g.grade_value}* — {g.status or 'pendente'}"
                    for g in grades
                )
                or "Nenhuma nota registrada."
            )

            doc_text = (
                f"*HISTÓRICO ACADÊMICO*\n\n"
                f"Aluno: *{student.full_name}*\n"
                f"RA: *{student.registration_number}*\n"
                f"Curso: *{student.course or 'N/I'}*\n\n"
                f"*Disciplinas:*\n{grade_lines}\n\n"
                f"Data de emissão: *{today}*\n"
                f"_Documento gerado digitalmente pelo sistema IGS._"
            )
        else:
            doc_text = (
                f"Documento do tipo *{doc_type}* solicitado para *{student.full_name}*. "
                f"A secretaria foi notificada e entrará em contato."
            )

        await whatsapp_service.send_text_message(
            tenant.whatsapp_phone_number_id,
            tenant.whatsapp_token,
            contact.phone_number,
            doc_text,
        )
        logger.info("Documento %s gerado para %s", doc_type, student.full_name)


async def _send_weekly_pdf_report_async():
    """Gera PDF com metricas da semana e envia por email para admins."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services.email_service import send_email
    from app.services.report_service import get_conversation_report, rows_to_pdf

    since = datetime.now(timezone.utc) - timedelta(days=7)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        tenants = await db.execute(select(Tenant).where(Tenant.is_active))
        for tenant in tenants.scalars().all():
            try:
                rows = await get_conversation_report(db, tenant.id, since, now)
                if not rows:
                    continue

                pdf_bytes = rows_to_pdf(rows, title=f"Relatorio Semanal - {tenant.name}")

                # Envia para admins do tenant
                admins = await db.execute(
                    select(User).where(
                        User.tenant_id == tenant.id,
                        User.role.in_(["admin", "manager"]),
                        User.is_active,
                    )
                )
                for admin in admins.scalars().all():
                    send_email(
                        to=admin.email,
                        subject=f"Relatorio Semanal IGS - {tenant.name}",
                        body=(
                            f"<h2>Relatorio Semanal</h2>"
                            f"<p>Periodo: {since.strftime('%d/%m/%Y')} a {now.strftime('%d/%m/%Y')}</p>"
                            f"<p>Total de conversas: <strong>{len(rows)}</strong></p>"
                            f"<p>Em anexo o relatorio completo em PDF.</p>"
                        ),
                        attachment=pdf_bytes,
                        attachment_name=f"relatorio_semanal_{now.strftime('%Y%m%d')}.pdf",
                    )

                logger.info("Relatorio PDF enviado para tenant %s", tenant.slug)
            except Exception as exc:
                logger.error("Erro relatorio PDF tenant %s: %s", tenant.id, exc)


async def _check_sla_async():
    from app.dependencies import WorkerSessionLocal as AsyncSessionLocal
    from app.services.sla_service import check_sla_breaches

    async with AsyncSessionLocal() as db:
        breaches = await check_sla_breaches(db)
        if breaches:
            logger.warning("SLA violado em %d tickets", len(breaches))
            from app.tasks.push_tasks import send_sla_breach_push_task

            for b in breaches:
                logger.warning(
                    "SLA breach: tenant=%s ticket=%s priority=%s deadline=%s",
                    b["tenant_id"],
                    b["protocol"],
                    b["priority"],
                    b["deadline"],
                )
                if b.get("ticket_id"):
                    send_sla_breach_push_task.delay(str(b["ticket_id"]), str(b["tenant_id"]))
        await db.commit()
