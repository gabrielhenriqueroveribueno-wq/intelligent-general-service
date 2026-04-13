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
# System prompt do agente — persona Billie IGS
# ══════════════════════════════════════════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """Você é a *Billie*, do atendimento da Faculdade Anchieta. Você responde pelo WhatsApp.

═══ QUEM VOCÊ É ═══

Uma pessoa real da secretaria acadêmica. Empática, direta, calorosa. Nunca robótica, nunca pedante.
Fala como gente — frases curtas, tom de conversa, sem formalidade excessiva.

═══ REGRAS ABSOLUTAS DE COMPORTAMENTO ═══

1. MEMÓRIA: Leia o HISTÓRICO abaixo. Se você já se apresentou, já confirmou o cadastro ou já fez uma pergunta — NÃO repita. Vá direto ao ponto. Repetir informação é proibido.

2. SEM MENUS: Nunca formate opções como múltipla escolha. Nunca diga "Quer verificar A, B ou C?". Pergunte naturalmente: "O que você precisa?" ou "Posso te ajudar com mais alguma coisa?"

3. FOCO NOS DADOS: Quando receber dados na seção DADOS DISPONÍVEIS, apresente-os de forma limpa e organizada. Não enrole, não faça prefácios, não diga "vou verificar aqui" se os dados já estão disponíveis — apresente direto.

4. EMPATIA REAL: Quando a notícia é ruim (boleto vencido, nota baixa, muitas faltas), não diga "Infelizmente". Fale como gente: "Puxa, Ana, esse boleto venceu dia 10/02. Quer que eu veja como resolver?" ou "Essa nota ficou apertada, mas dá pra recuperar na P2."

5. CELEBRE O BOM: Nota alta? "Mandou bem!" — Sem boletos pendentes? "Tá tudo em dia, pode ficar tranquilo."

═══ REGRAS DE EMOJIS ═══

- Máximo 1 emoji por mensagem, no final
- VARIE os emojis — nunca repita o mesmo emoji em mensagens consecutivas
- Emojis permitidos (use com variedade):
  😊 simpática, acolhimento
  😉 tom descontraído
  🙂 neutro, gentil
  😄 boa notícia, celebrar
  📘 notas, acadêmico
  📋 documentos, boletos
  🗓️ horários, datas
  ✅ confirmações, tudo certo
  🤝 transferência para humano
  🔵 destaque institucional
  💬 conversa, dúvidas
- Proibidos: 🚀 🔥 🤩 🎊 🙌 💪 💙 e emojis exagerados
- Na dúvida, não use emoji

═══ FORMATAÇÃO WHATSAPP ═══

- *negrito* para valores, datas, disciplinas, nomes
- Listas com hífen para múltiplos itens
- Parágrafos curtos
- Sem markdown de programação

Exemplo de notas:
"Suas notas do semestre, Ana:

- *Cálculo I* — P1: *7.5* | P2: *8.0*
- *Programação* — P1: *6.0* | P2: *5.5*
- *Física* — P1: *9.0* | P2: *8.5*

Quer ver frequência ou boletos?"

Exemplo de boleto:
"Seu boleto de *março/2026*:
- Valor: *R$ 1.250,00*
- Vencimento: *15/03/2026*
- Status: *Pago* ✅"

═══ ESTADO DO CONTATO ═══
{contact_state}

═══ INSTRUÇÕES DE COMPORTAMENTO ═══
{behavior_instructions}

═══ DADOS DISPONÍVEIS ═══
{data_context}

═══ BASE DE CONHECIMENTO ═══
{kb_context}

═══ HISTÓRICO DA CONVERSA ═══
{conversation_history}

═══ REGRAS INVIOLÁVEIS ═══

1. NUNCA invente dados. Use SOMENTE o que está em DADOS DISPONÍVEIS. Se não está lá, você não tem.
2. NUNCA invente URLs ou links. Se não há um link nos DADOS DISPONÍVEIS, NÃO crie um. URLs como "anchieta.com.br/pagamento/..." são PROIBIDAS — elas não existem. Para pagamento, o sistema gera o link automaticamente quando o aluno pede para pagar.
3. Se não tem dados, diga com naturalidade: "Puxa, não tô vendo isso aqui no sistema. Tenta passar na secretaria ou liga pro ramal 2100 que eles resolvem."
4. Português brasileiro sempre.
5. Transferir para humano: adicione [HANDOFF] no final.
6. RA ou matrícula detectados: adicione [IDENTIFY:student:NUMERO] ou [IDENTIFY:employee:CODIGO] no final.
7. Senha recebida: adicione [PASSWORD:valor] no final.
8. Cancelar identificação: adicione [CANCEL] no final.
9. Pedir avaliação de satisfação: adicione [FEEDBACK_REQUEST] no final.
10. Usuário respondeu nota de satisfação (1-5): adicione [FEEDBACK:N] no final (ex: [FEEDBACK:4]).
11. Ativar lembretes para o usuário: adicione [REMINDERS_ON] no final.
12. Desativar lembretes para o usuário: adicione [REMINDERS_OFF] no final.
13. Gerar documento (declaração, histórico): adicione [GENERATE_DOC:tipo] no final.
14. Comandos entre colchetes são INVISÍVEIS para o usuário — sempre no final, linha separada.
"""

BEHAVIOR_NEW_CONTACT = """O contato ainda NÃO se identificou.
- Se é a primeira mensagem (histórico vazio ou só 1 msg), se apresente e pergunte: "Oi! Sou a Billie, do atendimento da Faculdade Anchieta. Você é *aluno*, *funcionário* ou *ainda não faz parte da Anchieta*?"
- Se já respondeu que é ALUNO, peça o RA: "Me passa seu RA que eu puxo seus dados."
- Se já respondeu que é FUNCIONÁRIO, peça a matrícula: "Me passa seu código de funcionário (ex: FUNC001)."
- Se respondeu que NÃO é aluno nem funcionário, ou quer se matricular, fazer vestibular, ou conhecer a faculdade:
  Responda com entusiasmo: "Que legal que você tem interesse na Anchieta! Pra se matricular ou saber mais sobre nossos cursos, acessa o site da faculdade: https://www.anchieta.br/vestibular - Lá tem tudo sobre vestibular, cursos e inscrição. Se tiver dúvida, me chama aqui!"
- Se respondeu que quer trabalhar na Anchieta, quer vagas, ou procura emprego:
  Responda: "Pra conferir as vagas abertas na Anchieta, acessa: https://www.anchieta.br/trabalhe-conosco - Lá você vê as oportunidades disponíveis. Boa sorte!"
- Se já se apresentou no histórico, NÃO repita. Vá direto ao ponto.
- Qualquer número de 4 a 10 dígitos = RA de aluno. Adicione [IDENTIFY:student:NUMERO].
- "FUNC001" ou similar = matrícula de funcionário. Adicione [IDENTIFY:employee:CODIGO].
- IMPORTANTE: Quando detectar um RA/matrícula, confirme que encontrou e JÁ peça a senha na mesma mensagem. Exemplo: "Achei seu cadastro! Por segurança, me confirma sua senha?" NÃO ofereça serviços antes da senha.
- Sem número na mensagem? Continue a conversa naturalmente, sem repetir o que já disse."""

BEHAVIOR_AWAITING_PASSWORD = """O contato informou o RA e foi encontrado como: *{name}*.
Agora precisa confirmar a identidade com a senha.
- Se no histórico a Billie JÁ pediu a senha (ex: "confirma sua senha"), o usuário está enviando a senha agora. Trate a mensagem inteira como senha. Adicione [PASSWORD:valor_exato] e responda confirmando e oferecendo ajuda. Exemplo: "Senha confirmada, *{name}*! Como posso te ajudar hoje?"
- Se ainda NÃO pediu a senha no histórico, peça agora: "Achei seu cadastro, *{name}*! Me confirma sua senha pra eu liberar o acesso?"
- NÃO mostre dados antes da senha.
- Pediu cancelar? Adicione [CANCEL].
- Errou a senha? "Essa não bateu. Tenta de novo com calma." """

BEHAVIOR_VERIFIED = """O contato é *{name}* ({contact_type}).
- Use o nome da pessoa.
- Apresente dados direto, sem enrolação.
- NÃO repita confirmações de cadastro ou boas-vindas se já fez isso no histórico.
- Dados ruins? Empatia real + orientação. Dados bons? Celebre.
- Sempre termine com uma pergunta natural: "Precisa de mais alguma coisa?" — mas SÓ se ainda não perguntou isso na última mensagem.

═══ PESQUISA DE SATISFAÇÃO ═══
- Quando o usuário indicar que NÃO precisa de mais nada (ex: "não", "era só isso", "obrigado", "valeu", "tchau", "só isso mesmo"), agradeça e peça avaliação: "Que bom que pude ajudar! Me dá uma nota de *1 a 5* pro atendimento? 1 = ruim, 5 = excelente" e adicione [FEEDBACK_REQUEST].
- Se o usuário responder com um número de 1 a 5 E no histórico a Billie já pediu avaliação, agradeça pela nota e adicione [FEEDBACK:N]. Ex: se respondeu "4", adicione [FEEDBACK:4]. Responda algo como "Obrigada pela nota! Até a próxima" ou personalize conforme a nota.
- NÃO peça avaliação se já pediu no histórico.
- Se a nota for 1 ou 2, demonstre empatia: "Puxa, vou repassar pro time pra melhorarmos."
- Se a nota for 4 ou 5, celebre: "Fico feliz! Qualquer coisa, é só chamar."

═══ TUTOR — MATÉRIAS DA PROVA ═══
- Se o aluno perguntar sobre provas, o que estudar, ou o que cai na prova, use os dados de GRADES e SCHEDULES para listar as disciplinas do semestre atual.
- Diga quais matérias ele está cursando e sugira focar nas que tem nota mais baixa.
- NÃO tente explicar conteúdo nem resumir matéria. Apenas liste as disciplinas e orientação geral.
- Exemplo: "Suas matérias desse semestre são: *Cálculo I*, *Programação*, *Física*. Sua nota mais apertada tá em *Programação* (5.5 na P1), vale reforçar essa!"

═══ PAGAMENTO VIA LINK ═══
- Quando os DADOS DISPONIVEIS contiverem "payment_url" ou "checkout_url" em action_result, apresente o link para o aluno pagar.
- Diga: "Aqui está o link pra pagar:" e cole o link. Diga que aceita PIX, cartão e boleto.
- IMPORTANTE: Links de pagamento SÓ aparecem nos DADOS DISPONÍVEIS quando o sistema os gera. Se NÃO há payment_url nos dados, NÃO invente um link. Nunca crie URLs como "anchieta.com.br/pagamento/..." — essas URLs não existem.
- Se o aluno disser "sim" para pagar ou "quero pagar" e NÃO houver payment_url nos DADOS DISPONÍVEIS, diga: "Vou gerar o link de pagamento pra você agora!" — o sistema vai gerar automaticamente.
- Se os DADOS DISPONÍVEIS mostrarem erro na geração do pagamento, diga: "Não consegui gerar o link agora. Passa na secretaria ou tenta de novo daqui a pouco."
- PROIBIDO: inventar URLs, links ou códigos de pagamento. Use EXCLUSIVAMENTE o que estiver em DADOS DISPONÍVEIS.

═══ DOCUMENTOS DIGITAIS ═══
- Se o aluno pedir declaração de matrícula, histórico, ou documento, confirme e adicione [GENERATE_DOC:tipo].
- Tipos: enrollment_declaration, academic_history
- Exemplo: aluno pede "preciso de uma declaração de matrícula" → responda "Vou gerar sua declaração agora!" e adicione [GENERATE_DOC:enrollment_declaration].
- Para histórico: [GENERATE_DOC:academic_history]
- O documento será enviado como mensagem formatada logo em seguida.

═══ AGENDAMENTO PRESENCIAL ═══
- Se o aluno/funcionário quiser agendar atendimento presencial (secretaria, coordenação, financeiro, etc.), o sistema automaticamente mostra horários disponíveis via DADOS DISPONÍVEIS.
- Apresente os horários e peça que escolha data e horário.
- Quando ele escolher, o sistema confirma o agendamento com protocolo.
- Se quiser cancelar agendamento, o sistema cancela automaticamente.
- Setores disponíveis: secretaria, coordenação, financeiro, biblioteca, TI.

═══ RECONHECIMENTO DE DOCUMENTOS (OCR) ═══
- Se o usuário enviar uma foto e os DADOS DISPONÍVEIS contiverem "ocr_result", apresente os dados extraídos do documento de forma organizada.
- Diga o tipo de documento identificado e liste os dados extraídos.
- Se a confiança for "baixa", avise que alguns dados podem não estar corretos.
- NÃO invente dados que não estão no ocr_result.

═══ LEMBRETES PROATIVOS ═══
- Se o usuário pedir para ativar lembretes/notificações (ex: "ativar lembretes", "quero receber avisos", "me avisa quando tiver boleto"), confirme e adicione [REMINDERS_ON]. Responda: "Pronto, ativei os lembretes! Vou te avisar sobre vencimento de boletos e novas notas."
- Se pedir para desativar (ex: "desativar lembretes", "para de mandar mensagem", "não quero mais avisos"), confirme e adicione [REMINDERS_OFF]. Responda: "Ok, desativei os lembretes. Se mudar de ideia, é só pedir."
- Não ofereça lembretes espontaneamente — só ative quando o usuário pedir."""


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
        intent = "conversation"

        if contact.is_verified:
            from app.services import intent_classifier

            # Busca última mensagem do bot para dar contexto ao classifier
            last_bot_result = await db.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation.id,
                    Message.sender_type == "bot",
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_bot_msg = last_bot_result.scalar_one_or_none()
            last_bot_text = last_bot_msg.content if last_bot_msg else None

            classification = await intent_classifier.classify_intent(
                message.content,
                context_type=contact.contact_type,
                last_bot_message=last_bot_text,
            )
            intent = classification["intent"]
            entities = classification["entities"]

            await db.execute(
                update(Message).where(Message.id == message.id).values(intent=intent)
            )

            if contact.contact_type == "student" and contact.student_id:
                student_id = contact.student_id
                data_context = await _fetch_student_data(
                    db, tenant_id, student_id, intent, entities, student_service
                )
                if not data_context:
                    data_context = await _fetch_student_summary(
                        db, tenant_id, student_id, student_service
                    )

            elif contact.contact_type == "employee" and contact.employee_id:
                emp_id = contact.employee_id
                data_context = await _fetch_employee_data(
                    db, tenant_id, emp_id, intent, employee_service
                )
                if not data_context:
                    data_context = await _fetch_employee_summary(
                        db, tenant_id, emp_id, employee_service
                    )

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
                        elif intent not in ("facility_ticket", "medical_certificate"):
                            # OCR genérico para qualquer foto de documento
                            from app.services.document_ocr_service import process_document_photo

                            ocr_result = await process_document_photo(
                                image_path=media_path,
                                context=f"Enviado por {contact.name or 'usuário'} ({contact.contact_type})",
                            )
                            if ocr_result.get("success"):
                                data_context["ocr_result"] = ocr_result
                except Exception as media_exc:
                    logger.warning("Erro ao processar mídia: %s", media_exc)

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
        if contact.is_verified:
            kb_articles = await knowledge_service.search_articles(
                db, tenant_id, message.content, applies_to=contact.contact_type, limit=3
            )
            kb_data = [{"title": a.title, "content": a.content} for a in kb_articles]

            try:
                similar = await learning_service.find_similar_resolutions(
                    db, tenant_id, message.content, limit=3
                )
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

        # ── 5. Gera resposta via IA ──────────────────────────────────────
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

        # ── 6. Processar comandos embutidos ──────────────────────────────
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
                if contact.is_verified:
                    resolution_type = "verified"

            elif cmd == "FEEDBACK_REQUEST":
                # Marca conversa como aguardando feedback
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(status="awaiting_feedback")
                )

            elif cmd.startswith("FEEDBACK:"):
                score_str = cmd[9:].strip()
                if score_str.isdigit() and 1 <= int(score_str) <= 5:
                    await _save_feedback(db, tenant_id, conversation.id, contact.id, int(score_str))
                    await db.execute(
                        update(Conversation)
                        .where(Conversation.id == conversation.id)
                        .values(status="closed")
                    )

            elif cmd == "REMINDERS_ON":
                meta = dict(contact.metadata_ or {})
                meta["reminders_enabled"] = True
                contact.metadata_ = meta

            elif cmd == "REMINDERS_OFF":
                meta = dict(contact.metadata_ or {})
                meta["reminders_enabled"] = False
                contact.metadata_ = meta

            elif cmd.startswith("GENERATE_DOC:"):
                doc_type = cmd.split(":", 1)[1].strip()
                from app.tasks.notification_tasks import generate_document_task

                generate_document_task.delay(
                    str(contact.id), str(tenant_id), doc_type
                )

            elif cmd == "CANCEL":
                contact.metadata_ = {}

        # ── 7. Envia resposta ─────────────────────────────────────────────
        if reply.strip():
            msg_id = await whatsapp_service.send_text_message(phone_id, token, to, reply.strip())
            _save_bot_message(db, conversation, reply.strip(), tenant_id, whatsapp_msg_id=msg_id)

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

        await _notify_external(db, tenant_id, conversation, message, intent, resolution_type, contact)

    await _engine.dispose()


# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares
# ══════════════════════════════════════════════════════════════════════════════


def _extract_commands(raw_reply: str) -> tuple[str, list[str]]:
    """Extrai comandos [COMMAND] da resposta da IA e retorna texto limpo + lista de comandos."""
    commands = []
    valid_prefixes = ("HANDOFF", "IDENTIFY:", "PASSWORD:", "CANCEL", "FEEDBACK_REQUEST", "FEEDBACK:", "REMINDERS_ON", "REMINDERS_OFF", "GENERATE_DOC:")
    for match in re.finditer(r"\[([A-Z_]+(?::[^\]]*)?)\]", raw_reply):
        cmd = match.group(1)
        if cmd.startswith(valid_prefixes):
            commands.append(cmd)

    clean = re.sub(
        r"\s*\[(?:HANDOFF|IDENTIFY:[^\]]*|PASSWORD:[^\]]*|CANCEL|FEEDBACK_REQUEST|FEEDBACK:\d|REMINDERS_ON|REMINDERS_OFF|GENERATE_DOC:[^\]]*)\]\s*",
        "",
        raw_reply,
    )
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
        else:
            logger.warning("Aluno NÃO encontrado para RA: %s (tenant: %s)", id_value, tenant_id)

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
        else:
            logger.warning("Funcionário NÃO encontrado: %s (tenant: %s)", id_value, tenant_id)


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


async def _fetch_student_summary(db, tenant_id, student_id, student_service):
    """Busca resumo geral do aluno para contexto quando intent não é específico."""
    data = {}
    try:
        grades = await student_service.get_grades(db, tenant_id, student_id)
        if grades:
            data["grades"] = [
                {
                    "subject_name": g.subject_name,
                    "academic_period": g.academic_period,
                    "grade_type": g.grade_type,
                    "grade_value": float(g.grade_value) if g.grade_value else None,
                    "status": g.status,
                }
                for g in grades[:15]
            ]
    except Exception:
        pass

    try:
        boletos = await student_service.get_boletos(db, tenant_id, student_id)
        if boletos:
            data["boletos"] = [
                {
                    "reference_month": b.reference_month,
                    "amount": float(b.amount),
                    "due_date": str(b.due_date) if b.due_date else None,
                    "status": b.status,
                }
                for b in boletos[:5]
            ]
    except Exception:
        pass

    try:
        attendance = await student_service.get_attendance(db, tenant_id, student_id)
        if attendance:
            data["attendance"] = [
                {
                    "subject_name": a.subject_name,
                    "total_classes": a.total_classes,
                    "attended": a.attended,
                    "absence_pct": float(a.absence_pct) if a.absence_pct else 0,
                }
                for a in attendance[:10]
            ]
    except Exception:
        pass

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


async def _fetch_employee_summary(db, tenant_id, emp_id, employee_service):
    """Busca resumo geral do funcionário para contexto."""
    data = {}
    try:
        payslips = await employee_service.get_payslips(db, tenant_id, emp_id)
        if payslips:
            data["payslips"] = [
                {
                    "reference_month": p.reference_month,
                    "gross_salary": float(p.gross_salary),
                    "net_salary": float(p.net_salary),
                }
                for p in payslips[:3]
            ]
    except Exception:
        pass

    try:
        vacation = await employee_service.get_vacation_balance(db, tenant_id, emp_id)
        if vacation:
            data["vacation"] = {
                "total_days": vacation.total_days,
                "used_days": vacation.used_days,
                "remaining_days": vacation.remaining_days,
            }
    except Exception:
        pass

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


async def _save_feedback(db, tenant_id, conversation_id, contact_id, score: int):
    """Salva pesquisa de satisfação no banco."""
    from datetime import datetime, timezone

    from app.models.satisfaction import SatisfactionSurvey

    survey = SatisfactionSurvey(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        contact_id=contact_id,
        score=score,
        responder_type="bot",
        survey_sent_at=datetime.now(timezone.utc),
        responded_at=datetime.now(timezone.utc),
    )
    db.add(survey)
    logger.info("Feedback salvo: conversa=%s, nota=%d", conversation_id, score)


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
