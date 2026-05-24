# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import json
import logging
import os
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "grade_query",  # Consulta de notas
    "attendance_query",  # Consulta de frequência
    "schedule_query",  # Consulta de horários
    "boleto_query",  # Consulta/2ª via de boleto
    "enrollment_query",  # Situação de matrícula
    "payslip_query",  # Consulta de holerite
    "vacation_query",  # Saldo de férias
    "time_record_query",  # Registro de ponto
    "hr_request",  # Solicitação de RH (atestado, declaração)
    "faq",  # Pergunta geral / FAQ
    "human_handoff",  # Pedido de atendente humano
    "greeting",  # Saudação inicial
    "verification",  # Verificação de identidade (RA/matrícula)
    "generate_boleto",  # Gerar boleto de pagamento
    "enrollment_request",  # Pedido de matrícula/rematrícula
    "document_request",  # Solicitar documentos (declaração, histórico, diploma)
    "class_enrollment",  # Inscrição em disciplinas
    "grade_appeal",  # Recurso de nota
    "transfer_request",  # Pedido de transferência
    "scholarship_query",  # Consulta sobre bolsas
    "internship_query",  # Estágio/TCC
    "event_registration",  # Inscrição em eventos
    "library_query",  # Consulta biblioteca (empréstimo, renovação, multa)
    "financial_negotiation",  # Negociação de débitos
    "certificate_request",  # Solicitar certificados
    "slide_generate",  # Professor solicita criação de slides/apresentação
    "slide_update",  # Professor solicita atualização de slides existentes
    "generate_pix",  # Gerar código PIX para boleto
    "facility_ticket",  # Chamado de infraestrutura (com foto opcional)
    "library_renewal",  # Renovação de empréstimo na biblioteca
    "tutor_question",  # Dúvida acadêmica para tutor IA
    "medical_certificate",  # Envio de atestado médico (foto)
    "feedback_response",  # Resposta de pesquisa de satisfação (nota 1-5)
    "enable_reminders",  # Ativar lembretes proativos
    "disable_reminders",  # Desativar lembretes proativos
    "farewell",  # Despedida / encerramento de atendimento
    "schedule_appointment",  # Agendar atendimento presencial
    "cancel_appointment",  # Cancelar agendamento
    "document_ocr",  # Reconhecimento de documento via foto
    "open_ticket",  # Abrir chamado de suporte geral (problema não categorizado)
    "unknown",  # Intenção não reconhecida
]

# ══════════════════════════════════════════════════════════════════════════════
# Classifier system prompt — carregado de arquivo externo (gitignored em prod).
# Configure BILLIE_CLASSIFIER_PROMPT_FILE no .env. Fallback:
# backend/prompts/billie_classifier.txt → billie_classifier.stub.txt.
# ══════════════════════════════════════════════════════════════════════════════

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
_CLASSIFIER_STUB_PATH = _PROMPTS_DIR / "billie_classifier.stub.txt"


def _load_classifier_prompt() -> str:
    candidates = []
    env_path = os.environ.get("BILLIE_CLASSIFIER_PROMPT_FILE", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_PROMPTS_DIR / "billie_classifier.txt")

    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
            logger.info("Classifier prompt carregado de: %s", path)
            return content
        except FileNotFoundError:
            continue

    try:
        content = _CLASSIFIER_STUB_PATH.read_text(encoding="utf-8")
        logger.warning(
            "BILLIE_CLASSIFIER_PROMPT_FILE não encontrado. Usando stub público — "
            "configure o prompt real em produção."
        )
        return content
    except FileNotFoundError:
        logger.error("Stub do classifier também não encontrado. Usando fallback mínimo.")
        return (
            "Classifique a mensagem em uma das intenções: "
            + ", ".join(VALID_INTENTS)
            + '. Responda APENAS JSON: {"intent": "nome", "entities": {}}'
        )


CLASSIFIER_SYSTEM_PROMPT = _load_classifier_prompt()


async def classify_intent(
    message: str,
    context_type: Optional[str] = None,
    last_bot_message: Optional[str] = None,
) -> dict:
    """
    Classifica a intenção da mensagem usando o provider de IA configurado.
    Retorna: {"intent": str, "entities": dict}
    """
    context_hint = ""
    if context_type == "student":
        context_hint = "\nContexto: usuário é um aluno."
    elif context_type == "employee":
        context_hint = "\nContexto: usuário é um funcionário/RH."
    elif context_type == "teacher":
        context_hint = "\nContexto: usuário é um professor. Se pedir para criar/gerar slides ou apresentação, use slide_generate. Se pedir para atualizar/modificar slides existentes, use slide_update."

    # Se a mensagem é curta (ex: "sim", "quero"), usa o contexto da última msg do bot
    user_msg = message
    if last_bot_message and len(message.strip()) <= 30:
        user_msg = (
            f"[Última mensagem do bot: {last_bot_message[:150]}]\nUsuário respondeu: {message}"
        )

    try:
        result = await ai_complete(
            system=CLASSIFIER_SYSTEM_PROMPT + context_hint,
            message=user_msg,
            max_tokens=settings.CLAUDE_CLASSIFIER_MAX_TOKENS,
        )

        raw = result.text

        # Extrai JSON da resposta
        if "{" in raw:
            json_str = raw[raw.index("{") : raw.rindex("}") + 1]
            parsed = json.loads(json_str)
            intent = parsed.get("intent", "unknown")
            if intent not in VALID_INTENTS:
                intent = "unknown"
            return {"intent": intent, "entities": parsed.get("entities", {})}

    except Exception as e:
        logger.warning("Erro ao classificar intenção: %s", e)

    return {"intent": "unknown", "entities": {}}
