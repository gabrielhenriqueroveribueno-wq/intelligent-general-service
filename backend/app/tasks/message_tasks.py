"""
Tarefa principal de processamento de mensagens do WhatsApp.

Fluxo:
1. Recebe ID da mensagem salva no banco
2. Identifica o contato (aluno/funcionário)
3. Classifica a intenção via Claude
4. Busca dados no banco conforme a intenção
5. Gera resposta com Claude (RAG estruturado)
6. Envia via WhatsApp API
7. Registra tokens, intenção e tempo de resposta
"""

import asyncio
import logging
import time
import uuid

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

WELCOME_MSG = (
    "Olá! 👋 Sou o assistente virtual da instituição.\n\n"
    "Para te identificar, por favor informe:\n"
    "• Se for *aluno*: seu RA (ex: RA123456)\n"
    "• Se for *funcionário*: seu número de matrícula (ex: FUNC001)"
)

MENU_MSG = (
    "Não entendi sua solicitação. 😅 Posso te ajudar com:\n\n"
    "📚 *Alunos:* notas, frequência, horários, boletos, matrícula\n"
    "👔 *Funcionários:* holerite, férias, ponto, solicitações\n\n"
    "Digite sua dúvida ou *falar com atendente* para suporte humano."
)

HANDOFF_MSG = (
    "Entendido! 🙋 Vou te transferir para um de nossos atendentes.\n"
    "Um ticket foi aberto com o protocolo *{protocol}*.\n"
    "Em breve entraremos em contato. Obrigado pela paciência! 🙏"
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_incoming_message(self, message_id: str):
    """Processa uma mensagem recebida do WhatsApp."""
    try:
        asyncio.run(_process_message_async(message_id))
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            _persist_failed_task(self, message_id, exc)
            raise


def _persist_failed_task(task, message_id: str, exc: Exception):
    """Persiste tarefa falha no banco para inspeção posterior."""
    import traceback as tb

    from app.tasks.dlq_tasks import save_failed_task_async

    asyncio.run(
        save_failed_task_async(
            task_id=task.request.id or "unknown",
            task_name=task.name,
            args={"message_id": message_id},
            error_message=str(exc),
            traceback=tb.format_exc(),
            retry_count=task.max_retries,
        )
    )


async def _process_message_async(message_id: str):
    from sqlalchemy import select, update

    from app.dependencies import AsyncSessionLocal
    from app.middleware.metrics_middleware import (
        ai_tokens_used_total,
        messages_processed_total,
        response_time_histogram,
    )
    from app.models.conversation import Contact, Conversation, Message
    from app.models.tenant import Tenant
    from app.services import (
        ai_service,
        employee_service,
        intent_classifier,
        knowledge_service,
        student_service,
        ticket_service,
        whatsapp_service,
    )

    start_time = time.perf_counter()

    async with AsyncSessionLocal() as db:
        # Carrega a mensagem
        result = await db.execute(select(Message).where(Message.id == uuid.UUID(message_id)))
        message = result.scalar_one_or_none()
        if not message:
            logger.error("Mensagem não encontrada: %s", message_id)
            return

        # Carrega a conversa e contato
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            return

        contact_result = await db.execute(
            select(Contact).where(Contact.id == conversation.contact_id)
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            return

        # Carrega o tenant (para obter phone_number_id e access_token)
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == message.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
            logger.warning("Tenant sem configuração WhatsApp: %s", message.tenant_id)
            return

        phone_id = tenant.whatsapp_phone_number_id
        token = tenant.whatsapp_token  # em produção, descriptografar aqui
        to = contact.phone_number
        tenant_id = message.tenant_id

        # ── 1. Verificação de identidade (primeiro contato) ────────────────
        if not contact.is_verified:
            await whatsapp_service.send_text_message(phone_id, token, to, WELCOME_MSG)
            _save_bot_message(db, conversation, WELCOME_MSG, tenant_id)
            await db.commit()
            return

        # ── 2. Classificação de intenção ───────────────────────────────────
        classification = await intent_classifier.classify_intent(
            message.content, context_type=contact.contact_type
        )
        intent = classification["intent"]
        entities = classification["entities"]

        await db.execute(update(Message).where(Message.id == message.id).values(intent=intent))

        # ── 3. Human handoff ───────────────────────────────────────────────
        if intent == "human_handoff":
            ticket = await ticket_service.create_ticket(
                db,
                tenant_id=tenant_id,
                subject="Solicitação de atendimento humano",
                priority="medium",
                contact_id=contact.id,
                conversation_id=conversation.id,
            )
            reply = HANDOFF_MSG.format(protocol=ticket.protocol_number)
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(status="waiting_agent")
            )
            await whatsapp_service.send_text_message(phone_id, token, to, reply)
            _save_bot_message(db, conversation, reply, tenant_id)
            await db.commit()
            return

        # ── 4. Busca de dados conforme intenção ───────────────────────────
        data_context = {}
        if contact.contact_type == "student" and contact.student_id:
            student_id = contact.student_id
            if intent == "grade_query":
                grades = await student_service.get_grades(
                    db, tenant_id, student_id, subject=entities.get("subject")
                )
                data_context["grades"] = [
                    {
                        "subject_name": g.subject_name,
                        "academic_period": g.academic_period,
                        "grade_type": g.grade_type,
                        "grade_value": float(g.grade_value) if g.grade_value else None,
                        "status": g.status,
                    }
                    for g in grades
                ]
            elif intent == "attendance_query":
                attendance = await student_service.get_attendance(db, tenant_id, student_id)
                data_context["attendance"] = [
                    {
                        "subject_name": a.subject_name,
                        "academic_period": a.academic_period,
                        "total_classes": a.total_classes,
                        "attended": a.attended,
                        "absence_pct": float(a.absence_pct) if a.absence_pct else 0,
                    }
                    for a in attendance
                ]
            elif intent == "boleto_query":
                boletos = await student_service.get_boletos(db, tenant_id, student_id)
                data_context["boletos"] = [
                    {
                        "reference_month": b.reference_month,
                        "amount": float(b.amount),
                        "due_date": str(b.due_date) if b.due_date else None,
                        "status": b.status,
                    }
                    for b in boletos[:3]
                ]

        elif contact.contact_type == "employee" and contact.employee_id:
            emp_id = contact.employee_id
            if intent == "payslip_query":
                payslips = await employee_service.get_payslips(db, tenant_id, emp_id)
                data_context["payslips"] = [
                    {
                        "reference_month": p.reference_month,
                        "gross_salary": float(p.gross_salary),
                        "net_salary": float(p.net_salary),
                    }
                    for p in payslips[:3]
                ]
            elif intent == "vacation_query":
                vacation = await employee_service.get_vacation_balance(db, tenant_id, emp_id)
                if vacation:
                    data_context["vacation"] = {
                        "total_days": vacation.total_days,
                        "used_days": vacation.used_days,
                        "remaining_days": vacation.remaining_days,
                        "deadline_date": str(vacation.deadline_date)
                        if vacation.deadline_date
                        else None,
                    }

        # ── 5. Busca KB ───────────────────────────────────────────────────
        kb_articles = await knowledge_service.search_articles(
            db, tenant_id, message.content, applies_to=contact.contact_type, limit=3
        )
        kb_data = [{"title": a.title, "content": a.content} for a in kb_articles]

        # ── 6. Gera resposta ───────────────────────────────────────────────
        if not data_context and not kb_data and intent not in ("greeting", "faq"):
            reply = MENU_MSG
            tokens = 0
            resolution_type = "menu"
        else:
            # Histórico de mensagens recentes
            from app.models.conversation import Message as MsgModel

            history_result = await db.execute(
                select(MsgModel)
                .where(MsgModel.conversation_id == conversation.id)
                .order_by(MsgModel.created_at.desc())
                .limit(5)
            )
            history = [
                {"sender_type": m.sender_type, "content": m.content}
                for m in reversed(history_result.scalars().all())
            ]

            bot_name = (tenant.settings or {}).get("bot_name", "Assistente")
            api_key = tenant.claude_api_key or None

            reply, tokens = await ai_service.generate_response(
                message=message.content,
                intent=intent,
                data_context=data_context,
                kb_articles=kb_data,
                conversation_history=history,
                bot_name=bot_name,
                api_key=api_key,
            )
            resolution_type = "auto"

            # Atualiza tokens usados na mensagem
            await db.execute(
                update(Message).where(Message.id == message.id).values(ai_tokens_used=tokens)
            )

            if tokens:
                ai_tokens_used_total.labels(tenant_id=str(tenant_id), call_type="generate").inc(
                    tokens
                )

        # ── 7. Envia resposta ──────────────────────────────────────────────
        msg_id = await whatsapp_service.send_text_message(phone_id, token, to, reply)
        _save_bot_message(db, conversation, reply, tenant_id, whatsapp_msg_id=msg_id)

        # Atualiza last_message_at
        from datetime import datetime, timezone

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(last_message_at=datetime.now(timezone.utc))
        )

        # Métricas
        elapsed = time.perf_counter() - start_time
        messages_processed_total.labels(
            tenant_id=str(tenant_id),
            intent=intent,
            resolution_type=resolution_type,
        ).inc()
        response_time_histogram.labels(tenant_id=str(tenant_id)).observe(elapsed)

        await db.commit()
        logger.info("Mensagem %s processada em %.2fs (intent=%s)", message_id, elapsed, intent)

        # ── 8. Notifica painel via WebSocket (Redis pub/sub) ──────────────
        try:
            import json as _json

            import redis.asyncio as aioredis

            from app.config import settings as _settings
            from app.services.ws_manager import REDIS_CHANNEL

            _r = aioredis.from_url(_settings.REDIS_URL, decode_responses=True)
            await _r.publish(
                REDIS_CHANNEL,
                _json.dumps(
                    {
                        "type": "new_message",
                        "tenant_id": str(tenant_id),
                        "conversation_id": str(conversation.id),
                        "intent": intent,
                        "resolution_type": resolution_type,
                    }
                ),
            )
            await _r.aclose()
        except Exception as _exc:
            logger.warning("Falha ao publicar evento WS: %s", _exc)


def _save_bot_message(db, conversation, content: str, tenant_id, whatsapp_msg_id=None):
    from app.models.conversation import Message

    msg = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        sender_type="bot",
        content=content,
        whatsapp_msg_id=whatsapp_msg_id,
    )
    db.add(msg)
