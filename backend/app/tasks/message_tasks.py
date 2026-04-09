"""
Tarefa principal de processamento de mensagens do WhatsApp.

Abordagem: Agente Conversacional
- TODA mensagem passa pela IA, sem respostas enlatadas
- A IA decide o que fazer com base no contexto completo
- Verificação de identidade é conversacional (IA extrai RA da conversa)
- O sistema busca dados e a IA formata a resposta naturalmente
"""

import asyncio
import json
import logging
import re
import time
import uuid

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# System prompt do agente — o "cérebro" de toda interação
# ══════════════════════════════════════════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """Você é a Billie, atendente da Faculdade Anchieta. Você trabalha na secretaria e adora ajudar os alunos.

QUEM VOCÊ É:
- Você é gente como a gente — carismática, acolhedora, com jeitinho brasileiro
- Trata todo mundo pelo nome quando sabe, faz o aluno se sentir em casa
- Fala de um jeito leve e natural, como se estivesse conversando no WhatsApp mesmo
- Usa emojis de forma natural (como qualquer pessoa no WhatsApp), mas sem exagero
- Suas respostas são curtas porque é WhatsApp — ninguém quer ler um textão
- Você demonstra interesse genuíno em ajudar, não é atendimento frio de call center
- Se alguém tá com problema, você se preocupa de verdade
- Você tem um toque de humor leve quando cabe, mas sempre com respeito

EXEMPLOS DO SEU JEITO DE FALAR:
- "Oi! Tudo bem? Sou a Billie, da secretaria 😊 Como posso te ajudar?"
- "Achei aqui suas notas! Olha só..."
- "Xiii, esse boleto tá vencido... mas calma que a gente resolve!"
- "Boa notícia: suas notas tão ótimas! 🎉"
- "Me passa seu RA que eu puxo seus dados aqui rapidinho"

ESTADO ATUAL DO CONTATO:
{contact_state}

INSTRUÇÕES DE COMPORTAMENTO:
{behavior_instructions}

DADOS DISPONÍVEIS:
{data_context}

BASE DE CONHECIMENTO:
{kb_context}

HISTÓRICO DA CONVERSA:
{conversation_history}

REGRAS IMPORTANTES:
1. NUNCA invente dados (notas, faltas, valores, datas). Use SOMENTE os dados fornecidos acima.
2. Se não tem dados, diga algo como "Hmm, não tô encontrando isso aqui... Melhor passar na secretaria pra gente verificar pessoalmente!"
3. Responda SEMPRE em português brasileiro.
4. Se a pessoa quiser falar com um humano/atendente, adicione [HANDOFF] no final.
5. Se identificar um RA ou matrícula na mensagem do usuário, adicione [IDENTIFY:student:NUMERO] ou [IDENTIFY:employee:CODIGO] no FINAL da sua resposta, em linha separada.
6. Se o contato está aguardando senha e o usuário enviou a senha, adicione [PASSWORD:valor] no FINAL.
7. Se o usuário quiser cancelar/recomeçar a identificação, adicione [CANCEL] no final.
8. Os comandos entre colchetes são INVISÍVEIS pro usuário — coloque sempre no FINAL, separados do texto.
"""

# Instruções específicas por estado do contato
BEHAVIOR_NEW_CONTACT = """O contato ainda NÃO se identificou.
- SEMPRE se apresente pelo nome ("Oi! Eu sou a Billie, da secretaria da Anchieta!") e já emende perguntando como pode ajudar e pedindo o RA ou matrícula. Tudo numa mensagem só, fluida — não mande só "oi" e espere.
- Mantenha a conversa fluindo: depois de se apresentar, já pergunte se é aluno ou funcionário, o que precisa, etc. Não deixe a pessoa no vácuo.
- Se a pessoa mandar o RA de qualquer jeito — "meu RA é 1234567", "RA: 1234567", "1234567", "sou o aluno 1234567", "ok vou enviar meu RA 1234567" — você DEVE extrair o número e adicionar [IDENTIFY:student:NUMERO] no final.
- Números soltos de 4 a 10 dígitos = RA de aluno. Adicione [IDENTIFY:student:NUMERO].
- Se disser "FUNC001" ou similar = matrícula de funcionário. Adicione [IDENTIFY:employee:CODIGO].
- Se a mensagem não contém nenhum número de identificação, converse normalmente e peça o RA de forma natural.
- NUNCA mande mensagem sem resposta. Mesmo que não entenda, converse e oriente.
- IMPORTANTE: Essa apresentação é só nas primeiras mensagens. Se no histórico você já se apresentou, NÃO repita — vá direto ao ponto."""

BEHAVIOR_AWAITING_PASSWORD = """O contato informou o RA e foi encontrado como: {name}
Agora precisa confirmar com a senha.
- Peça a senha de forma carinhosa e natural ("Achei seu cadastro, {name}! 😊 Agora por segurança, me confirma sua senha rapidinho?").
- Já adiante que depois da senha vocês podem resolver tudo — dê continuidade, não fique só esperando.
- Quando o usuário enviar a senha (qualquer texto curto que não seja uma pergunta), adicione [PASSWORD:valor_exato] no final.
- Se pedir para cancelar, adicione [CANCEL].
- NÃO mostre dados acadêmicos antes da senha ser confirmada.
- Seja paciente se errar a senha — encoraje a tentar de novo."""

BEHAVIOR_VERIFIED = """O contato está verificado como: {name} ({contact_type})
- Trate pelo nome! Seja calorosa.
- Pode ajudar com tudo: notas, frequência, boletos, horários, biblioteca, etc.
- Apresente os dados de forma conversacional e organizada — não despeje uma lista fria.
- Se tiver boas notícias (notas altas, sem pendências), comemore com o aluno!
- Se tiver problemas (boleto atrasado, muitas faltas), seja empática e oriente.
- Quando não tiver dados carregados pra responder, diga que vai verificar.
- SEMPRE dê continuidade: depois de responder, pergunte se precisa de mais alguma coisa, se quer ver outra informação, etc. Mantenha a conversa viva até a pessoa dizer que está tudo certo.
- Exemplos de continuidade: "Quer ver mais alguma coisa?", "Posso te ajudar com algo mais?", "Se precisar de qualquer coisa, tô aqui!"."""


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
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker as async_sessionmaker_sync

    from app.config import settings
    from app.middleware.metrics_middleware import (
        ai_tokens_used_total,
        messages_processed_total,
        response_time_histogram,
    )
    from app.models.conversation import Contact, Conversation, Message
    from app.models.tenant import Tenant
    from app.services import (
        employee_service,
        knowledge_service,
        learning_service,
        metrics_service,
        student_service,
        task_executor,
        ticket_service,
        transcription_service,
        whatsapp_service,
    )
    from app.services.ai_client import ai_complete

    start_time = time.perf_counter()

    # Cria engine fresh para este event loop (evita "Future attached to different loop")
    from sqlalchemy.ext.asyncio import async_sessionmaker

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _SessionLocal() as db:
        # ── Carrega mensagem, conversa, contato e tenant ──────────────────
        result = await db.execute(select(Message).where(Message.id == uuid.UUID(message_id)))
        message = result.scalar_one_or_none()
        if not message:
            logger.error("Mensagem não encontrada: %s", message_id)
            return

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

        tenant_result = await db.execute(select(Tenant).where(Tenant.id == message.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant or not tenant.whatsapp_phone_number_id or not tenant.whatsapp_token:
            logger.warning("Tenant sem configuração WhatsApp: %s", message.tenant_id)
            return

        phone_id = tenant.whatsapp_phone_number_id
        token = tenant.whatsapp_token
        to = contact.phone_number
        tenant_id = message.tenant_id

        # ── 0. Transcrição de áudio ───────────────────────────────────────
        if message.message_type == "audio" and message.whatsapp_media_id:
            try:
                from app.services import media_service

                audio_bytes = await media_service.download_media(message.whatsapp_media_id, token)
                if audio_bytes:
                    transcription = await transcription_service.transcribe_audio(
                        audio_bytes, message.media_mime_type or "audio/ogg"
                    )
                    await db.execute(
                        update(Message)
                        .where(Message.id == message.id)
                        .values(content=transcription, message_type="audio_transcribed")
                    )
                    message.content = transcription
            except Exception as audio_exc:
                logger.warning("Falha ao transcrever áudio: %s", audio_exc)

        # ── 1. Montar contexto do contato ─────────────────────────────────
        contact_meta = contact.metadata_ or {}
        pending_student_id = contact_meta.get("pending_student_id")
        pending_employee_id = contact_meta.get("pending_employee_id")
        pending_name = contact_meta.get("pending_name", "")

        if contact.is_verified:
            contact_state = f"Verificado como: {contact.name} ({contact.contact_type})"
            behavior = BEHAVIOR_VERIFIED.format(
                name=contact.name, contact_type=contact.contact_type
            )
        elif pending_student_id or pending_employee_id:
            contact_state = f"Aguardando senha — identificado como: {pending_name}"
            behavior = BEHAVIOR_AWAITING_PASSWORD.format(name=pending_name)
        else:
            contact_state = "Não identificado (primeiro contato ou RA não informado)"
            behavior = BEHAVIOR_NEW_CONTACT

        # ── 2. Buscar dados se verificado ─────────────────────────────────
        data_context = {}
        intent = "conversation"  # default — a IA é quem "decide"

        if contact.is_verified:
            # Classificar intenção para buscar dados relevantes
            from app.services import intent_classifier

            classification = await intent_classifier.classify_intent(
                message.content, context_type=contact.contact_type
            )
            intent = classification["intent"]
            entities = classification["entities"]

            await db.execute(
                update(Message).where(Message.id == message.id).values(intent=intent)
            )

            # Buscar dados do aluno
            if contact.contact_type == "student" and contact.student_id:
                student_id = contact.student_id
                data_context = await _fetch_student_data(
                    db, tenant_id, student_id, intent, entities, student_service
                )

            # Buscar dados do funcionário
            elif contact.contact_type == "employee" and contact.employee_id:
                emp_id = contact.employee_id
                data_context = await _fetch_employee_data(
                    db, tenant_id, emp_id, intent, employee_service
                )

            # Handle media attachments
            if message.message_type == "image" and message.whatsapp_media_id:
                try:
                    from app.services import media_service

                    media_path = await media_service.fetch_and_store_media(
                        media_id=message.whatsapp_media_id,
                        mime_type=message.media_mime_type or "image/jpeg",
                        access_token=token,
                    )
                    if media_path:
                        data_context["attached_media_url"] = media_path
                        if intent == "facility_ticket":
                            from app.services.ticket_service import attach_media_to_latest_ticket

                            await attach_media_to_latest_ticket(
                                db, tenant_id, contact.id, media_path
                            )
                        if intent == "medical_certificate" and contact.employee_id:
                            from app.services.hr_vision_service import process_medical_certificate

                            vision_result = await process_medical_certificate(
                                db=db,
                                tenant_id=tenant_id,
                                employee_id=contact.employee_id,
                                image_path=media_path,
                                access_token=token,
                            )
                            if vision_result:
                                data_context["action_result"] = vision_result
                except Exception as media_exc:
                    logger.warning("Erro ao processar mídia: %s", media_exc)

            # Executar ações
            if task_executor.is_action_intent(intent):
                try:
                    action_result = await task_executor.execute_action(
                        db=db,
                        tenant_id=tenant_id,
                        contact_id=contact.id,
                        conversation_id=conversation.id,
                        intent=intent,
                        entities=entities,
                        student_id=(
                            contact.student_id
                            if contact.contact_type == "student"
                            else None
                        ),
                    )
                    if action_result:
                        data_context["action_result"] = action_result
                except Exception as action_exc:
                    logger.warning("Erro ao executar ação %s: %s", intent, action_exc)

        # ── 3. Busca KB e resoluções similares ────────────────────────────
        kb_data = []
        similar_resolutions_data = []
        if contact.is_verified:
            kb_articles = await knowledge_service.search_articles(
                db, tenant_id, message.content, applies_to=contact.contact_type, limit=3
            )
            kb_data = [{"title": a.title, "content": a.content} for a in kb_articles]

            try:
                similar = await learning_service.find_similar_resolutions(
                    db, tenant_id, message.content, limit=3
                )
                similar_resolutions_data = [
                    {
                        "problem_description": r.problem_description,
                        "resolution_description": r.resolution_description,
                    }
                    for r in similar
                ]
            except Exception:
                pass

        # ── 4. Histórico da conversa ──────────────────────────────────────
        from app.models.conversation import Message as MsgModel

        history_result = await db.execute(
            select(MsgModel)
            .where(MsgModel.conversation_id == conversation.id)
            .order_by(MsgModel.created_at.desc())
            .limit(10)
        )
        history = [
            {"sender_type": m.sender_type, "content": m.content}
            for m in reversed(history_result.scalars().all())
        ]
        history_str = "\n".join(
            f"{'Usuário' if m['sender_type'] == 'user' else 'Billie'}: {m['content'] or ''}"
            for m in history
        )

        # ── 5. Gera resposta via IA (agente conversacional) ───────────────
        data_str = _format_data_for_agent(data_context) if data_context else "Nenhum dado carregado."
        kb_str = (
            "\n".join(f"[{a['title']}] {a['content']}" for a in kb_data[:3])
            if kb_data
            else "Nenhum artigo relevante."
        )

        system_prompt = AGENT_SYSTEM_PROMPT.format(
            contact_state=contact_state,
            behavior_instructions=behavior,
            data_context=data_str,
            kb_context=kb_str,
            conversation_history=history_str or "Início da conversa.",
        )

        api_key = tenant.claude_api_key or None
        ai_result = await ai_complete(
            system=system_prompt,
            message=message.content or "",
            max_tokens=800,
            api_key=api_key,
        )

        raw_reply = ai_result.text
        tokens = ai_result.tokens_used

        # ── 6. Processar comandos embutidos na resposta da IA ─────────────
        reply, commands = _extract_commands(raw_reply)
        resolution_type = "agent"

        for cmd in commands:
            if cmd == "HANDOFF":
                ticket = await ticket_service.create_ticket(
                    db,
                    tenant_id=tenant_id,
                    subject="Solicitação de atendimento humano",
                    priority="medium",
                    contact_id=contact.id,
                    conversation_id=conversation.id,
                )
                reply += f"\n\nProtocolo: *{ticket.protocol_number}*"
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(status="waiting_agent")
                )
                resolution_type = "handoff"

            elif cmd.startswith("IDENTIFY:"):
                parts = cmd.split(":", 2)
                if len(parts) == 3:
                    id_type, id_value = parts[1], parts[2]
                    await _handle_identification(
                        db, contact, tenant_id, id_type, id_value.strip()
                    )

            elif cmd.startswith("PASSWORD:"):
                password = cmd[9:].strip()
                await _handle_password(db, contact, password)
                # Se verificou com sucesso, atualiza a reply
                if contact.is_verified:
                    resolution_type = "verified"

            elif cmd == "CANCEL":
                contact.metadata_ = {}

        # ── 7. Envia resposta ─────────────────────────────────────────────
        if reply.strip():
            msg_id = await whatsapp_service.send_text_message(phone_id, token, to, reply.strip())
            _save_bot_message(db, conversation, reply.strip(), tenant_id, whatsapp_msg_id=msg_id)

        # Atualiza tokens e métricas
        await db.execute(
            update(Message).where(Message.id == message.id).values(
                ai_tokens_used=tokens, intent=intent
            )
        )

        from datetime import datetime, timezone

        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(last_message_at=datetime.now(timezone.utc))
        )

        elapsed = time.perf_counter() - start_time
        messages_processed_total.labels(
            tenant_id=str(tenant_id), intent=intent, resolution_type=resolution_type
        ).inc()
        response_time_histogram.labels(tenant_id=str(tenant_id)).observe(elapsed)

        if tokens:
            ai_tokens_used_total.labels(tenant_id=str(tenant_id), call_type="agent").inc(tokens)

        try:
            await metrics_service.record_response_time(
                db=db,
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                message_id=message.id,
                responder_type="bot",
                response_time=elapsed,
            )
        except Exception:
            pass

        await db.commit()
        logger.info("Mensagem %s processada em %.2fs (intent=%s)", message_id, elapsed, intent)

        # ── 8. Webhook + WebSocket notifications ─────────────────────────
        await _notify_external(db, tenant_id, conversation, message, intent, resolution_type, contact)

    # Fecha o engine para liberar conexões deste event loop
    await _engine.dispose()


# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares
# ══════════════════════════════════════════════════════════════════════════════


def _extract_commands(raw_reply: str) -> tuple[str, list[str]]:
    """Extrai comandos [COMMAND] da resposta da IA e retorna texto limpo + lista de comandos."""
    commands = []
    # Encontra todos os comandos entre colchetes
    for match in re.finditer(r"\[([A-Z_]+(?::[^\]]*)?)\]", raw_reply):
        cmd = match.group(1)
        if cmd.startswith(("HANDOFF", "IDENTIFY:", "PASSWORD:", "CANCEL")):
            commands.append(cmd)

    # Remove comandos do texto visível
    clean = re.sub(r"\s*\[(?:HANDOFF|IDENTIFY:[^\]]*|PASSWORD:[^\]]*|CANCEL)\]\s*", "", raw_reply)
    return clean.strip(), commands


async def _handle_identification(db, contact, tenant_id, id_type: str, id_value: str):
    """Busca aluno/funcionário e marca como pendente de senha."""
    from sqlalchemy import select

    if id_type == "student":
        from app.models.student import Student

        result = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_id,
                Student.registration_number == id_value,
            )
        )
        student = result.scalar_one_or_none()
        if student:
            contact.metadata_ = {
                "pending_student_id": str(student.id),
                "pending_name": student.full_name,
            }
            logger.info("Aluno identificado: %s (RA %s)", student.full_name, id_value)

    elif id_type == "employee":
        from app.models.employee import Employee

        result = await db.execute(
            select(Employee).where(
                Employee.tenant_id == tenant_id,
                Employee.employee_number == id_value.upper(),
            )
        )
        employee = result.scalar_one_or_none()
        if employee:
            contact.metadata_ = {
                "pending_employee_id": str(employee.id),
                "pending_name": employee.full_name,
            }
            logger.info("Funcionário identificado: %s (%s)", employee.full_name, id_value)


async def _handle_password(db, contact, password: str):
    """Valida senha e marca contato como verificado."""
    from sqlalchemy import select

    contact_meta = contact.metadata_ or {}
    pending_student_id = contact_meta.get("pending_student_id")
    pending_employee_id = contact_meta.get("pending_employee_id")

    if pending_student_id:
        from app.models.student import Student

        result = await db.execute(
            select(Student).where(Student.id == uuid.UUID(pending_student_id))
        )
        student = result.scalar_one_or_none()
        if student and _check_password(password, student.cpf):
            contact.student_id = student.id
            contact.contact_type = "student"
            contact.is_verified = True
            contact.name = student.full_name
            contact.metadata_ = {}
            logger.info("Aluno verificado com senha: %s", student.full_name)

    elif pending_employee_id:
        from app.models.employee import Employee

        result = await db.execute(
            select(Employee).where(Employee.id == uuid.UUID(pending_employee_id))
        )
        employee = result.scalar_one_or_none()
        if employee and _check_password(password, employee.cpf):
            contact.employee_id = employee.id
            contact.contact_type = "employee"
            contact.is_verified = True
            contact.name = employee.full_name
            contact.metadata_ = {}
            logger.info("Funcionário verificado com senha: %s", employee.full_name)


def _check_password(plain: str, stored_hash: str) -> bool:
    """Verifica senha — bcrypt hash ou últimos 6 dígitos do CPF."""
    if not stored_hash:
        return False
    if stored_hash.startswith("$2"):
        from app.utils.security import verify_password

        return verify_password(plain, stored_hash)
    # Fallback: últimos 6 dígitos do CPF como senha
    return plain == stored_hash[-6:] if len(stored_hash) >= 6 else plain == stored_hash


async def _fetch_student_data(db, tenant_id, student_id, intent, entities, student_service):
    """Busca dados do aluno conforme a intenção classificada."""
    data = {}

    if intent == "grade_query":
        grades = await student_service.get_grades(
            db, tenant_id, student_id, subject=entities.get("subject")
        )
        data["grades"] = [
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
        data["attendance"] = [
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
        data["boletos"] = [
            {
                "reference_month": b.reference_month,
                "amount": float(b.amount),
                "due_date": str(b.due_date) if b.due_date else None,
                "status": b.status,
            }
            for b in boletos[:5]
        ]

    elif intent == "schedule_query":
        student = await student_service.get_student_by_id(db, tenant_id, student_id)
        if student:
            schedules = await student_service.get_schedule(
                db, tenant_id, student.course, student.semester, "2026.1"
            )
            days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            data["schedules"] = [
                {
                    "day": days[s.day_of_week] if s.day_of_week < len(days) else str(s.day_of_week),
                    "subject_name": s.subject_name,
                    "start_time": str(s.start_time)[:5] if s.start_time else "",
                    "end_time": str(s.end_time)[:5] if s.end_time else "",
                    "room": s.room,
                    "professor": s.professor,
                }
                for s in schedules
            ]

    elif intent == "library_query":
        from app.services.library_service import get_library_summary

        data["library"] = await get_library_summary(db, tenant_id, student_id)

    return data


async def _fetch_employee_data(db, tenant_id, emp_id, intent, employee_service):
    """Busca dados do funcionário conforme a intenção classificada."""
    data = {}

    if intent == "payslip_query":
        payslips = await employee_service.get_payslips(db, tenant_id, emp_id)
        data["payslips"] = [
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
            data["vacation"] = {
                "total_days": vacation.total_days,
                "used_days": vacation.used_days,
                "remaining_days": vacation.remaining_days,
                "deadline_date": str(vacation.deadline_date) if vacation.deadline_date else None,
            }

    elif intent == "time_record_query":
        records = await employee_service.get_time_records(db, tenant_id, emp_id)
        data["time_records"] = [
            {
                "date": str(r.record_date) if r.record_date else "",
                "clock_in": str(r.clock_in.strftime("%H:%M")) if r.clock_in else "",
                "clock_out": str(r.clock_out.strftime("%H:%M")) if r.clock_out else "",
                "total_hours": float(r.total_hours) if r.total_hours else 0,
                "status": r.status,
            }
            for r in records[:10]
        ]

    elif intent == "hr_request":
        requests = await employee_service.get_hr_requests(db, tenant_id, emp_id)
        data["hr_requests"] = [
            {
                "type": r.request_type,
                "description": r.description,
                "status": r.status,
                "response": r.response_text,
            }
            for r in requests[:5]
        ]

    return data


def _format_data_for_agent(data: dict) -> str:
    """Formata dados para o contexto do agente."""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"=== {key.upper()} ===")
            for item in value:
                if isinstance(item, dict):
                    parts = [f"{k}: {v}" for k, v in item.items() if v is not None]
                    lines.append(f"  - {', '.join(parts)}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"=== {key.upper()} ===")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else "Nenhum dado disponível."


async def _notify_external(db, tenant_id, conversation, message, intent, resolution_type, contact):
    """Notifica sistemas externos (webhook + WebSocket)."""
    try:
        from app.services.webhook_delivery_service import dispatch_event

        await dispatch_event(
            db,
            tenant_id,
            "message.processed",
            {
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "intent": intent,
                "resolution_type": resolution_type,
                "contact_phone": contact.phone_number,
            },
        )
    except Exception as exc:
        logger.warning("Falha ao despachar webhook: %s", exc)

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
    except Exception as exc:
        logger.warning("Falha ao publicar evento WS: %s", exc)


def _save_bot_message(db, conversation, content: str, tenant_id, whatsapp_msg_id=None):
    from app.models.conversation import Message
    from app.utils.data_masking import mask_pii

    msg = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        sender_type="bot",
        content=mask_pii(content),
        whatsapp_msg_id=whatsapp_msg_id,
    )
    db.add(msg)
