# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Tarefa principal de processamento de mensagens do WhatsApp.

Abordagem: Agente Conversacional
- TODA mensagem passa pela IA, sem respostas enlatadas
- A IA decide o que fazer com base no contexto completo
- Verificação de identidade é conversacional (IA extrai RA da conversa)
- O sistema busca dados e a IA formata a resposta naturalmente
"""

import asyncio
import logging
import os
import re
import time
import uuid
from pathlib import Path

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# System prompt do agente — persona Billie IGS
# Carregado de arquivo externo (não comitado no repositório).
# Configure BILLIE_SYSTEM_PROMPT_FILE no .env com o caminho absoluto do arquivo.
# ══════════════════════════════════════════════════════════════════════════════

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
_STUB_PATH = _PROMPTS_DIR / "billie_agent.stub.txt"


def _load_system_prompt() -> str:
    """Load Billie's system prompt from the external file.

    Resolution order:
    1. Path in BILLIE_SYSTEM_PROMPT_FILE env var
    2. backend/prompts/billie_agent.txt (default, gitignored)
    3. backend/prompts/billie_agent.stub.txt (public stub, fallback)
    """
    candidates = []
    env_path = os.environ.get("BILLIE_SYSTEM_PROMPT_FILE", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_PROMPTS_DIR / "billie_agent.txt")

    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
            logger.info("Billie system prompt carregado de: %s", path)
            return content
        except FileNotFoundError:
            continue

    # Last resort: public stub
    try:
        content = _STUB_PATH.read_text(encoding="utf-8")
        logger.warning(
            "BILLIE_SYSTEM_PROMPT_FILE não encontrado. Usando stub público — "
            "configure o prompt real em produção."
        )
        return content
    except FileNotFoundError:
        logger.error("Stub de prompt também não encontrado. Usando fallback mínimo.")
        return (
            "Você é a Billie, assistente da Faculdade Anchieta.\n\n"
            "{contact_state}\n{behavior_instructions}\n"
            "{data_context}\n{kb_context}\n{conversation_history}"
        )


AGENT_SYSTEM_PROMPT = _load_system_prompt()


# ══════════════════════════════════════════════════════════════════════════════
# Behaviors (NEW_CONTACT / AWAITING_PASSWORD / VERIFIED) — carregados de arquivo
# externo. Configure BILLIE_BEHAVIORS_FILE no .env para apontar para o arquivo
# real (gitignored). Fallback: backend/prompts/billie_behaviors.txt, depois
# billie_behaviors.stub.txt.
# ══════════════════════════════════════════════════════════════════════════════

_BEHAVIORS_STUB_PATH = _PROMPTS_DIR / "billie_behaviors.stub.txt"
_BEHAVIOR_SECTION_RE = re.compile(r"^###\s*(\w+)\s*###\s*$", re.MULTILINE)


def _parse_behaviors(content: str) -> dict[str, str]:
    """Split a behaviors file into sections delimited by '### NAME ###' headers."""
    sections: dict[str, str] = {}
    parts = _BEHAVIOR_SECTION_RE.split(content)
    # parts = ["", name1, body1, name2, body2, ...]
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[name] = body
    return sections


def _load_behaviors() -> dict[str, str]:
    """Load behavior blocks from the external file.

    Resolution order:
    1. Path in BILLIE_BEHAVIORS_FILE env var
    2. backend/prompts/billie_behaviors.txt (default, gitignored)
    3. backend/prompts/billie_behaviors.stub.txt (public stub, fallback)
    """
    candidates = []
    env_path = os.environ.get("BILLIE_BEHAVIORS_FILE", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_PROMPTS_DIR / "billie_behaviors.txt")

    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
            logger.info("Billie behaviors carregados de: %s", path)
            return _parse_behaviors(content)
        except FileNotFoundError:
            continue

    try:
        content = _BEHAVIORS_STUB_PATH.read_text(encoding="utf-8")
        logger.warning(
            "BILLIE_BEHAVIORS_FILE não encontrado. Usando stub público — "
            "configure o arquivo real em produção."
        )
        return _parse_behaviors(content)
    except FileNotFoundError:
        logger.error("Stub de behaviors também não encontrado. Usando fallback mínimo.")
        return {
            "BEHAVIOR_NEW_CONTACT": "Contato não identificado. Peça RA ou código de funcionário.",
            "BEHAVIOR_AWAITING_PASSWORD": "Contato *{name}* aguardando senha.",
            "BEHAVIOR_VERIFIED": "Atendendo *{name}* ({contact_type}). Use apenas dados desta pessoa.",
        }


_BEHAVIORS = _load_behaviors()
BEHAVIOR_NEW_CONTACT = _BEHAVIORS.get("BEHAVIOR_NEW_CONTACT", "")
BEHAVIOR_AWAITING_PASSWORD = _BEHAVIORS.get("BEHAVIOR_AWAITING_PASSWORD", "")
BEHAVIOR_VERIFIED = _BEHAVIORS.get("BEHAVIOR_VERIFIED", "")


# ── Security gates ──────────────────────────────────────────────────────────
# Session expira após N dias — força re-verificação (RA + senha) caso o WhatsApp
# tenha sido transferido para outra pessoa ou ficado inativo por muito tempo.
SESSION_TTL_DAYS = 30
# Rate limit por contato verificado — protege contra spam que esgota budget de IA.
CONTACT_MSG_RATE_LIMIT_PER_HOUR = 30
# Cooldown após 2ª tentativa de leak/jailbreak: contato fica sem IA por 1h.
# Pode continuar mandando mensagem, mas só recebe orientação pra abrir ticket.
LEAK_COOLDOWN_SECONDS = 3600
LEAK_ATTEMPTS_THRESHOLD = 2  # 1ª = aviso; 2ª (>=) = cooldown


async def _check_session_expired(db, contact) -> bool:
    """Se a verificação do contato expirou, reseta is_verified e retorna True.

    Não derruba contatos legados sem `verified_at` (compatibilidade retroativa).
    """
    from datetime import datetime, timedelta, timezone

    if not contact.is_verified:
        return False
    meta = contact.metadata_ or {}
    verified_at_str = meta.get("verified_at")
    if not verified_at_str:
        return False  # contato legado — não força re-verificação
    try:
        verified_at = datetime.fromisoformat(verified_at_str)
    except (ValueError, TypeError):
        return False
    if datetime.now(timezone.utc) - verified_at <= timedelta(days=SESSION_TTL_DAYS):
        return False

    logger.info(
        "Sessão expirada para contact=%s (verified_at=%s) — forçando re-verificação",
        contact.id,
        verified_at_str,
    )
    contact.is_verified = False
    contact.student_id = None
    contact.employee_id = None
    contact.contact_type = "unknown"
    contact.metadata_ = {}
    await db.flush()
    return True


async def _check_contact_rate_limit(tenant_id, contact_id) -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes).

    Limita cada contato verificado a CONTACT_MSG_RATE_LIMIT_PER_HOUR msgs/hora.
    Fail-open: se o Redis estiver indisponível, permite passar.
    """
    try:
        import redis.asyncio as aioredis

        from app.config import settings as _settings

        r = aioredis.from_url(_settings.REDIS_URL, decode_responses=True)
        try:
            key = f"msg_rate:{tenant_id}:{contact_id}"
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 3600)
            if count > CONTACT_MSG_RATE_LIMIT_PER_HOUR:
                ttl = await r.ttl(key)
                return True, max(int(ttl), 60)
            return False, 0
        finally:
            await r.aclose()
    except Exception as exc:
        logger.debug("Rate limit Redis falhou (permitindo): %s", exc)
        return False, 0


async def _check_leak_cooldown(contact) -> tuple[bool, int]:
    """Retorna (em_cooldown, segundos_restantes) para o contato.

    Lê o timestamp `leak_cooldown_until` armazenado em contact.metadata_.
    Não escreve no DB aqui — apenas consulta. Fail-open em erro.
    """
    from datetime import datetime, timezone

    try:
        meta = contact.metadata_ or {}
        until_str = meta.get("leak_cooldown_until")
        if not until_str:
            return False, 0
        until = datetime.fromisoformat(until_str)
        now = datetime.now(timezone.utc)
        if now >= until:
            return False, 0
        remaining = int((until - now).total_seconds())
        return True, max(remaining, 60)
    except Exception as exc:
        logger.debug("Leak cooldown check falhou (permitindo): %s", exc)
        return False, 0


async def _handle_leak_attempt(db, contact) -> tuple[str, bool]:
    """Registra uma tentativa de leak. Retorna (mensagem_para_usuario, em_cooldown).

    1ª tentativa: contador++, aviso.
    2ª+ tentativa: contador++, ativa cooldown de LEAK_COOLDOWN_SECONDS.
    """
    from datetime import datetime, timedelta, timezone

    meta = dict(contact.metadata_ or {})
    attempts = int(meta.get("leak_attempts", 0)) + 1
    meta["leak_attempts"] = attempts

    if attempts >= LEAK_ATTEMPTS_THRESHOLD:
        until = datetime.now(timezone.utc) + timedelta(seconds=LEAK_COOLDOWN_SECONDS)
        meta["leak_cooldown_until"] = until.isoformat()
        contact.metadata_ = meta
        await db.flush()
        logger.warning(
            "Leak cooldown ATIVADO: contact=%s tentativas=%d até=%s",
            contact.id,
            attempts,
            until.isoformat(),
        )
        return (
            "⚠️ Identifiquei uma segunda tentativa de pedir informações confidenciais "
            "ou contornar minhas regras. Por segurança, seu acesso à assistente está "
            "suspenso por 1 hora. Durante esse período, se precisar de algo, envie "
            "*\"quero falar com atendente\"* para abrir um chamado com uma pessoa real.",
            True,
        )

    contact.metadata_ = meta
    await db.flush()
    logger.warning("Leak attempt registrado: contact=%s tentativas=%d", contact.id, attempts)
    return (
        "⚠️ Essa informação é confidencial e eu não posso compartilhar. "
        "Posso te ajudar com seus *próprios* dados (notas, boletos, horários, etc.) "
        "depois que você se identificar. Se insistir nesse tipo de pedido, seu acesso "
        "será suspenso por 1 hora.",
        False,
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
    from app.services.ai_client import ai_complete, ai_complete_safe  # noqa: F401

    start_time = time.perf_counter()

    from sqlalchemy.ext.asyncio import async_sessionmaker

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _session_local = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _session_local() as db:
        result = await db.execute(select(Message).where(Message.id == uuid.UUID(message_id)))
        message = result.scalar_one_or_none()
        if not message:
            logger.error("Mensagem não encontrada: %s", message_id)
            return

        # ── Análise de sentimento (apenas mensagens do usuário) ───────────
        if message.sender_type == "user" and message.content:
            from app.services.sentiment_service import analyze as analyze_sentiment

            sr = analyze_sentiment(message.content)
            await db.execute(
                update(Message)
                .where(Message.id == message.id)
                .values(sentiment=sr.label, sentiment_score=sr.score)
            )
            message.sentiment = sr.label
            message.sentiment_score = sr.score

            if sr.label == "negative" and sr.score <= -0.5:
                logger.info(
                    "Sentimento negativo detectado (score=%.2f): msg=%s", sr.score, message.id
                )

        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == message.conversation_id,
                Conversation.tenant_id == message.tenant_id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            logger.error(
                "Conversa não encontrada ou tenant mismatch: conv=%s tenant=%s",
                message.conversation_id,
                message.tenant_id,
            )
            return

        # ── Inibição do bot — agente humano ativo ────────────────────────
        # Se a conversa está aguardando agente ou um agente já assumiu,
        # o bot NÃO responde. A mensagem foi salva; apenas silenciamos.
        if conversation.assigned_agent_id or conversation.status == "waiting_agent":
            await db.commit()
            logger.info(
                "Bot inibido (agente humano): conv=%s status=%s",
                conversation.id,
                conversation.status,
            )
            await _engine.dispose()
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

        # ── Security gates: sessão expirada + rate-limit por contato ──────
        await _check_session_expired(db, contact)

        # ── Leak cooldown: bloqueio de 1h após 2 tentativas de leak/jailbreak ──
        _leak_blocked, _leak_remaining = await _check_leak_cooldown(contact)
        if _leak_blocked:
            _msg_text = (message.content or "").lower().strip()
            _wants_human = any(
                kw in _msg_text
                for kw in (
                    "atendente",
                    "humano",
                    "pessoa real",
                    "falar com algu",
                    "me transfere",
                    "quero falar",
                )
            )
            if _wants_human:
                # Permite handoff durante cooldown — usuário pode abrir ticket
                pass
            else:
                _min = max(1, _leak_remaining // 60)
                _canned = (
                    f"Seu acesso à assistente está suspenso por mais ~{_min} min "
                    f"devido a tentativas de pedir informações confidenciais. "
                    f"Envie *\"quero falar com atendente\"* para abrir um chamado."
                )
                _msg_id = await whatsapp_service.send_text_message(phone_id, token, to, _canned)
                _save_bot_message(db, conversation, _canned, tenant_id, whatsapp_msg_id=_msg_id)
                await db.execute(
                    update(Message)
                    .where(Message.id == message.id)
                    .values(ai_tokens_used=0, intent="leak_cooldown")
                )
                await db.commit()
                logger.warning(
                    "Mensagem bloqueada por leak cooldown: contact=%s restante=%ds",
                    contact.id,
                    _leak_remaining,
                )
                await _engine.dispose()
                return

        if contact.is_verified:
            _blocked, _retry_sec = await _check_contact_rate_limit(tenant_id, contact.id)
            if _blocked:
                _retry_min = max(1, _retry_sec // 60)
                _canned = (
                    f"Você atingiu o limite de mensagens por hora. "
                    f"Tenta de novo em ~{_retry_min} min. 🙏"
                )
                _msg_id = await whatsapp_service.send_text_message(phone_id, token, to, _canned)
                _save_bot_message(db, conversation, _canned, tenant_id, whatsapp_msg_id=_msg_id)
                from datetime import datetime as _dt_rl
                from datetime import timezone as _tz_rl

                await db.execute(
                    update(Message)
                    .where(Message.id == message.id)
                    .values(ai_tokens_used=0, intent="rate_limited")
                )
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(last_message_at=_dt_rl.now(_tz_rl.utc))
                )
                messages_processed_total.labels(
                    tenant_id=str(tenant_id),
                    intent="rate_limited",
                    resolution_type="blocked",
                ).inc()
                response_time_histogram.labels(tenant_id=str(tenant_id)).observe(
                    time.perf_counter() - start_time
                )
                await db.commit()
                logger.warning(
                    "Rate limit por contato: tenant=%s contact=%s retry_sec=%d",
                    tenant_id,
                    contact.id,
                    _retry_sec,
                )
                await _engine.dispose()
                return

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
            # Verifica bloqueio por excesso de tentativas de senha
            _locked_until_str = contact_meta.get("password_locked_until")
            _is_locked = False
            if _locked_until_str:
                try:
                    from datetime import datetime, timezone

                    _locked_until = datetime.fromisoformat(_locked_until_str)
                    if datetime.now(timezone.utc) < _locked_until:
                        _remaining = (
                            int((_locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
                            + 1
                        )
                        _is_locked = True
                except (ValueError, TypeError):
                    pass
            if _is_locked:
                contact_state = f"Aguardando senha — identificado como: {pending_name} — BLOQUEADO"
                behavior = (
                    f"A conta de {pending_name} está temporariamente bloqueada por excesso de "
                    f"tentativas de senha incorretas. Informe educadamente que o acesso ficará "
                    f"disponível em aproximadamente {_remaining} minutos e que não é necessário "
                    f"tentar novamente antes disso."
                )
            else:
                contact_state = f"Aguardando senha — identificado como: {pending_name}"
                behavior = BEHAVIOR_AWAITING_PASSWORD.format(name=pending_name)
        else:
            contact_state = "Não identificado (primeiro contato ou RA não informado)"
            behavior = BEHAVIOR_NEW_CONTACT

        # ── 2. Buscar dados se verificado ─────────────────────────────────
        data_context = {}
        intent = "conversation"

        # ── 2a. Interceptar feedback direto (sem IA) ─────────────────────
        # Fallback: se o status não é awaiting_feedback mas a última msg do bot pediu nota,
        # aceitar mesmo assim (caso o [FEEDBACK_REQUEST] não tenha sido incluído pelo Claude)
        _msg_stripped = (message.content or "").strip()
        _is_feedback_score = contact.is_verified and _msg_stripped in ("1", "2", "3", "4", "5")
        logger.info(
            "Feedback check: msg='%s', is_verified=%s, conv_status='%s', _is_feedback=%s",
            _msg_stripped,
            contact.is_verified,
            conversation.status,
            _is_feedback_score,
        )
        if _is_feedback_score:
            # Refresh conversation status from DB (may have been updated by previous task)
            await db.refresh(conversation)
            logger.info("Feedback check refreshed: conv_status='%s'", conversation.status)
            if conversation.status != "awaiting_feedback":
                # Fallback: check if last bot message asked for rating
                last_bot_msg = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id, Message.sender_type == "bot")
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                last_bot = last_bot_msg.scalar_one_or_none()
                logger.info(
                    "Feedback fallback: last_bot='%s'",
                    (last_bot.content or "")[:80] if last_bot else "None",
                )
                if not (
                    last_bot
                    and "nota de" in (last_bot.content or "").lower()
                    and "1 a 5" in (last_bot.content or "")
                ):
                    _is_feedback_score = False
                    logger.info("Feedback fallback: NOT a feedback score, skipping")

        if _is_feedback_score:
            score = int(message.content.strip())
            await _save_feedback(db, tenant_id, conversation.id, contact.id, score)
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(status="closed")
            )

            from datetime import datetime, timezone

            hour = datetime.now(timezone.utc).hour - 3  # UTC-3 (São Paulo)
            if hour < 0:
                hour += 24
            greeting = (
                "Tenha uma ótima noite!"
                if hour >= 18
                else ("Tenha um ótimo dia!" if hour >= 12 else "Tenha uma ótima manhã!")
            )

            first_name = contact.name.split()[0]
            thanks_map = {
                1: f"Poxa, sinto muito que não foi bom. Vou repassar pro time pra melhorarmos. Qualquer coisa, é só me chamar! {greeting} 🙂",
                2: f"Entendi, vou repassar pro time pra gente melhorar. Qualquer coisa, é só me chamar! {greeting} 🙂",
                3: f"Obrigada pela nota, {first_name}! Vamos trabalhar pra melhorar sempre. Qualquer coisa, é só me chamar! {greeting} 😊",
                4: f"Obrigada pela nota, {first_name}! Fico feliz que gostou. Qualquer coisa, é só me mandar mensagem! {greeting} 😄",
                5: f"Obrigada pela nota, {first_name}! Fico muito feliz! Qualquer coisa, é só me mandar mensagem. {greeting} 😊",
            }
            reply = thanks_map.get(score, f"Obrigada pela nota! {greeting}")

            msg_id = await whatsapp_service.send_text_message(phone_id, token, to, reply)
            _save_bot_message(db, conversation, reply, tenant_id, whatsapp_msg_id=msg_id)

            await db.execute(
                update(Message).where(Message.id == message.id).values(intent="feedback_response")
            )
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(last_message_at=datetime.now(timezone.utc))
            )

            elapsed = time.perf_counter() - start_time
            messages_processed_total.labels(
                tenant_id=str(tenant_id), intent="feedback_response", resolution_type="agent"
            ).inc()

            await db.commit()
            logger.info("Feedback direto processado: nota=%d, conversa=%s", score, conversation.id)
            await _engine.dispose()
            return

        # ── 2b. Interceptar despedida e forçar pedido de feedback (sem IA) ──
        _farewell_triggers = (
            "não",
            "nao",
            "não obrigado",
            "nao obrigado",
            "era só isso",
            "era so isso",
            "obrigado",
            "obrigada",
            "valeu",
            "tchau",
            "só isso",
            "so isso",
            "tá bom",
            "ta bom",
            "até mais",
            "ate mais",
            "nada mais",
            "é isso",
            "e isso",
            "só isso mesmo",
            "so isso mesmo",
            "não preciso",
            "nao preciso",
            "era isso",
            "brigado",
            "brigada",
            "flw",
            "falou",
            "vlw",
            "tmj",
        )
        _msg_lower = (message.content or "").strip().lower().rstrip("!.,;")
        if (
            contact.is_verified
            and conversation.status == "active"
            and _msg_lower
            and any(t in _msg_lower for t in _farewell_triggers)
        ):
            # Verifica se já pediu feedback nessa conversa
            _fb_check = await db.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation.id,
                    Message.sender_type == "bot",
                    Message.content.ilike("%nota de%1 a 5%"),
                )
                .limit(1)
            )
            if not _fb_check.scalar_one_or_none():
                from datetime import datetime
                from datetime import timezone as tz

                feedback_reply = f"Que bom que pude ajudar, {contact.name.split()[0]}! Me dá uma nota de *1 a 5* pro atendimento? 1 = ruim, 5 = excelente 😊"
                msg_id = await whatsapp_service.send_text_message(
                    phone_id, token, to, feedback_reply
                )
                _save_bot_message(
                    db, conversation, feedback_reply, tenant_id, whatsapp_msg_id=msg_id
                )
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(status="awaiting_feedback", last_message_at=datetime.now(tz.utc))
                )
                await db.execute(
                    update(Message).where(Message.id == message.id).values(intent="farewell")
                )
                await db.commit()
                logger.info(
                    "Farewell interceptado, feedback pedido direto (sem IA): conversa=%s",
                    conversation.id,
                )
                await _engine.dispose()
                return

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

            await db.execute(update(Message).where(Message.id == message.id).values(intent=intent))

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
                            contact.student_id if contact.contact_type == "student" else None
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
                await learning_service.find_similar_resolutions(
                    db, tenant_id, message.content, limit=3
                )
            except Exception:
                pass

        # ── 4. Histórico da conversa ──────────────────────────────────────
        from app.models.conversation import Message as MsgModel

        history_result = await db.execute(
            select(MsgModel)
            .where(
                MsgModel.conversation_id == conversation.id,
                MsgModel.tenant_id == tenant_id,
            )
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

        # ── Pre-gate: bloquear off-topic antes do LLM principal ──────────────
        # Só aplicado para contatos verificados. O fluxo de identificação
        # (RA, senha) é sempre considerado on-topic e passa direto.
        safe_input = _sanitize_user_input(message.content or "")
        if (
            contact.is_verified
            and safe_input
            and safe_input != "[conteúdo inválido]"
            and await _is_off_topic(safe_input)
        ):
            _canned = (
                "Sou especializada nos serviços da Anchieta. "
                "Posso te ajudar com notas, boletos, horários ou outros serviços da faculdade?"
            )
            _msg_id = await whatsapp_service.send_text_message(phone_id, token, to, _canned)
            _save_bot_message(db, conversation, _canned, tenant_id, whatsapp_msg_id=_msg_id)
            from datetime import datetime, timezone

            await db.execute(
                update(Message)
                .where(Message.id == message.id)
                .values(ai_tokens_used=0, intent="off_topic")
            )
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(last_message_at=datetime.now(timezone.utc))
            )
            elapsed = time.perf_counter() - start_time
            messages_processed_total.labels(
                tenant_id=str(tenant_id), intent="off_topic", resolution_type="blocked"
            ).inc()
            response_time_histogram.labels(tenant_id=str(tenant_id)).observe(elapsed)
            await db.commit()
            logger.info(
                "Pre-gate: mensagem off-topic bloqueada em %.2fs: '%s'",
                elapsed,
                safe_input[:60],
            )
            await _engine.dispose()
            return

        # ── 5. Gera resposta via IA ──────────────────────────────────────
        data_str = (
            _format_data_for_agent(data_context) if data_context else "Nenhum dado carregado."
        )
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
        ai_result = await ai_complete_safe(
            system=system_prompt,
            message=safe_input,
            max_tokens=800,
            api_key=api_key,
            user_message=safe_input,
            contact_name=contact.name,
            db=db,
            tenant_id=tenant_id,
        )

        raw_reply = ai_result.text
        tokens = ai_result.tokens_used

        # ── Output guardrail: detecta PII alheia/alucinada na resposta ────
        from app.utils.output_guardrail import SAFE_FALLBACK_REPLY, audit_llm_output

        _output_issues = audit_llm_output(raw_reply)
        if _output_issues:
            logger.error(
                "Output guardrail BLOQUEOU resposta: tenant=%s contact=%s issues=%s preview=%r",
                tenant_id,
                contact.id,
                _output_issues,
                raw_reply[:200],
            )
            raw_reply = SAFE_FALLBACK_REPLY

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
                # Push notification para agentes disponíveis
                try:
                    from app.tasks.push_tasks import send_handoff_push_task

                    send_handoff_push_task.delay(
                        str(conversation.id),
                        str(tenant_id),
                        contact.name or contact.phone_number or "Usuário",
                    )
                except Exception:
                    pass

            elif cmd == "LEAK_ATTEMPT":
                _leak_msg, _cooldown_now = await _handle_leak_attempt(db, contact)
                # Sobrescreve resposta da LLM com mensagem de segurança canônica
                reply = _leak_msg
                resolution_type = "leak_blocked"

            elif cmd.startswith("IDENTIFY:"):
                parts = cmd.split(":", 2)
                if len(parts) == 3:
                    id_type, id_value = parts[1], parts[2]
                    await _handle_identification(db, contact, tenant_id, id_type, id_value.strip())

            elif cmd.startswith("PASSWORD:"):
                password = cmd[9:].strip()
                await _handle_password(db, contact, password)
                if contact.is_verified:
                    resolution_type = "verified"
                    # Marca a conversa (ticket) com o tipo do login recém-autenticado.
                    # Após um [LOGOUT], esta é uma conversa nova, agora vinculada ao
                    # novo login (contact.name já foi atualizado em _handle_password).
                    await db.execute(
                        update(Conversation)
                        .where(Conversation.id == conversation.id)
                        .values(context_type=contact.contact_type)
                    )

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

                generate_document_task.delay(str(contact.id), str(tenant_id), doc_type)

            elif cmd == "CANCEL":
                contact.metadata_ = {}

            elif cmd == "LOGOUT":
                # Usuário pediu para sair / trocar de conta.
                # 1) Encerra a conversa atual (vira um "ticket" fechado no painel).
                # 2) Zera toda a identificação/verificação do contato.
                # A próxima mensagem do usuário não encontra conversa ativa no
                # webhook, então uma NOVA conversa é criada; ao se verificar de
                # novo, o atendimento passa a ficar sob o novo login.
                from datetime import datetime as _dt_logout
                from datetime import timezone as _tz_logout

                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(status="closed", closed_at=_dt_logout.now(_tz_logout.utc))
                )
                contact.is_verified = False
                contact.contact_type = "unknown"
                contact.student_id = None
                contact.employee_id = None
                contact.name = None
                contact.metadata_ = {}
                resolution_type = "logout"
                logger.info(
                    "Logout/troca de conta: contact=%s — conversa %s encerrada",
                    contact.id,
                    conversation.id,
                )

        # ── 7. Envia resposta ─────────────────────────────────────────────
        if reply.strip():
            msg_id = await whatsapp_service.send_text_message(phone_id, token, to, reply.strip())
            _save_bot_message(db, conversation, reply.strip(), tenant_id, whatsapp_msg_id=msg_id)

        await db.execute(
            update(Message)
            .where(Message.id == message.id)
            .values(ai_tokens_used=tokens, intent=intent)
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

        await _notify_external(
            db, tenant_id, conversation, message, intent, resolution_type, contact
        )

    await _engine.dispose()


# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares
# ══════════════════════════════════════════════════════════════════════════════


# Padrões de prompt injection e injeção de comandos do sistema
_CMD_INJECT_RE = re.compile(
    r"\[(HANDOFF|IDENTIFY:[^\]]*|PASSWORD:[^\]]*|CANCEL|FEEDBACK[^\]]*"
    r"|REMINDERS_(?:ON|OFF)|GENERATE_DOC:[^\]]*|LOGOUT)\]",
    re.IGNORECASE,
)
_INJECTION_RE = re.compile(
    r"\b(ignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|prompt|rules?)"
    r"|esque(?:ça?|ce?)\s+(as\s+)?instru[cç][oõ]es"
    r"|desconsider[ae]\s+(as\s+)?instru[cç][oõ]es"
    r"|act\s+as\b|atue?\s+como\b"
    r"|finja\s+(ser|que)\b"
    r"|pretend\s+(to\s+be|you\s+are)\b"
    r"|you\s+are\s+now\b|voc[eê]\s+[eé]\s+agora\b"
    r"|modo\s+desenvolvedor|developer\s+mode"
    r"|\bDAN\b|do\s+anything\s+now"
    r"|new\s+(persona|identity)|nova\s+persona"
    r"|system\s+prompt|prompt\s+injection)\b",
    re.IGNORECASE,
)


def _sanitize_user_input(text: str) -> str:
    """
    Sanitiza entrada do usuário antes de enviar ao LLM.
    - Remove tentativas de injetar comandos [COMMAND] do sistema
    - Neutraliza padrões comuns de prompt injection / jailbreak
    """
    if not text:
        return text
    # Remove tentativas de injetar comandos do sistema via texto do usuário
    clean = _CMD_INJECT_RE.sub("", text).strip()
    # Se detectar padrão de jailbreak, substitui todo o conteúdo
    if _INJECTION_RE.search(clean):
        logger.warning("Prompt injection detectado e neutralizado: '%s'", clean[:80])
        clean = "[conteúdo inválido]"
    return clean


_OFF_TOPIC_SYSTEM = (
    "Classify the user message as ON_TOPIC or OFF_TOPIC for a Brazilian university WhatsApp assistant.\n\n"
    "ON_TOPIC: grades, tuition fees, attendance, class schedules, enrollment, payslips, vacation, "
    "library, university documents, appointments, helpdesk, anything about university life.\n"
    "OFF_TOPIC: cooking recipes, jokes, weather, generic programming tutorials, personal advice, "
    "news, trivia, politics, religion, adult content, topics unrelated to the university.\n\n"
    "Short or ambiguous messages (greetings, numbers, 'ok', 'sim', 'não', 'oi') = ON_TOPIC.\n"
    "Reply ONLY with: ON_TOPIC or OFF_TOPIC"
)


async def _is_off_topic(text: str) -> bool:
    """Cheap pre-gate to reject clearly off-topic messages before the main Billie LLM.

    Uses a fast AI call (~5 output tokens). Falls back to False (allow) on
    any error — better to pass a borderline message than block a valid query.
    Only called for verified contacts; identification flow is always ON_TOPIC.
    """
    from app.services.ai_client import ai_complete

    try:
        result = await ai_complete(
            system=_OFF_TOPIC_SYSTEM,
            message=text[:500],
            max_tokens=5,
        )
        return "OFF_TOPIC" in result.text.upper()
    except Exception as exc:
        logger.debug("Pre-gate _is_off_topic falhou, permitindo mensagem: %s", exc)
        return False


def _extract_commands(raw_reply: str) -> tuple[str, list[str]]:
    """Extrai comandos [COMMAND] da resposta da IA e retorna texto limpo + lista de comandos."""
    commands = []
    valid_prefixes = (
        "HANDOFF",
        "IDENTIFY:",
        "PASSWORD:",
        "CANCEL",
        "FEEDBACK_REQUEST",
        "FEEDBACK:",
        "REMINDERS_ON",
        "REMINDERS_OFF",
        "GENERATE_DOC:",
        "LOGOUT",
    )
    for match in re.finditer(r"\[([A-Z_]+(?::[^\]]*)?)\]", raw_reply):
        cmd = match.group(1)
        if cmd.startswith(valid_prefixes):
            commands.append(cmd)

    clean = re.sub(
        r"\s*\[(?:HANDOFF|IDENTIFY:[^\]]*|PASSWORD:[^\]]*|CANCEL|FEEDBACK_REQUEST|FEEDBACK:\d|REMINDERS_ON|REMINDERS_OFF|GENERATE_DOC:[^\]]*|LOGOUT)\]\s*",
        "",
        raw_reply,
    )
    return clean.strip(), commands


async def _handle_identification(db, contact, tenant_id, id_type: str, id_value: str):
    """Busca aluno/funcionário e marca como pendente de senha. Limita tentativas para evitar enumeração de RAs."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    contact_meta = contact.metadata_ or {}
    now = datetime.now(timezone.utc)

    # ── Rate limiting — evita enumeração de RAs/matrículas ───────────
    identify_attempts = contact_meta.get("identify_attempts", 0)
    attempts_reset_str = contact_meta.get("identify_attempts_reset_at")
    if attempts_reset_str:
        try:
            reset_at = datetime.fromisoformat(attempts_reset_str)
            if now > reset_at:
                identify_attempts = 0  # Janela de 1h expirou — reseta
        except (ValueError, TypeError):
            identify_attempts = 0

    identify_attempts += 1

    if identify_attempts > 10:
        logger.warning(
            "Rate limit de identificação atingido: contact=%s tentativas=%d",
            contact.id,
            identify_attempts,
        )
        return  # Silently abort — não revela o motivo ao usuário

    # Base do metadata mantendo campos de rate limiting
    base_meta = {
        k: v
        for k, v in contact_meta.items()
        if k not in ("pending_student_id", "pending_employee_id", "pending_name")
    }
    base_meta["identify_attempts"] = identify_attempts
    if identify_attempts == 1:
        base_meta["identify_attempts_reset_at"] = (now + timedelta(hours=1)).isoformat()

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
                **base_meta,
                "pending_student_id": str(student.id),
                "pending_name": student.full_name,
            }
            logger.info("Aluno identificado: %s (RA %s)", student.full_name, id_value)
        else:
            contact.metadata_ = base_meta
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
                **base_meta,
                "pending_employee_id": str(employee.id),
                "pending_name": employee.full_name,
            }
            logger.info("Funcionário identificado: %s (%s)", employee.full_name, id_value)
        else:
            contact.metadata_ = base_meta
            logger.warning("Funcionário NÃO encontrado: %s (tenant: %s)", id_value, tenant_id)


async def _handle_password(db, contact, password: str):
    """Valida senha e marca contato como verificado. Máximo 3 tentativas em 15 minutos."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    contact_meta = contact.metadata_ or {}
    now = datetime.now(timezone.utc)

    # ── Rate limiting — evita brute force ────────────────────────────
    locked_until_str = contact_meta.get("password_locked_until")
    if locked_until_str:
        try:
            locked_until = datetime.fromisoformat(locked_until_str)
            if now < locked_until:
                logger.warning("Tentativa de senha bloqueada (rate limit): contact=%s", contact.id)
                return  # Billie já informa o bloqueio via contact_state
        except (ValueError, TypeError):
            pass

    pending_student_id = contact_meta.get("pending_student_id")
    pending_employee_id = contact_meta.get("pending_employee_id")
    password_attempts = contact_meta.get("password_attempts", 0) + 1
    verified = False

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
            contact.metadata_ = {"verified_at": now.isoformat()}
            verified = True
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
            contact.metadata_ = {"verified_at": now.isoformat()}
            verified = True
            logger.info("Funcionário verificado com senha: %s", employee.full_name)

    if not verified:
        # Incrementa contador — bloqueia após 3 tentativas por 15 minutos
        meta = {k: v for k, v in contact_meta.items()}
        meta["password_attempts"] = password_attempts
        if password_attempts >= 3:
            meta["password_locked_until"] = (now + timedelta(minutes=15)).isoformat()
            meta["password_attempts"] = 0
            logger.warning(
                "Contact bloqueado após %d tentativas de senha incorretas: %s",
                password_attempts,
                contact.id,
            )
        contact.metadata_ = meta


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

    elif intent == "enrollment_query":
        student = await student_service.get_student_by_id(db, tenant_id, student_id)
        if student:
            data["enrollment"] = {
                "course": student.course,
                "semester": student.semester,
                "enrollment_status": student.enrollment_status,
                "enrollment_date": str(student.enrollment_date)
                if student.enrollment_date
                else None,
                "registration_number": student.registration_number,
            }

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
