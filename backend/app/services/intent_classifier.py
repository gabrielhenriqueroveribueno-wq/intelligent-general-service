import json
import logging
from typing import Optional

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

VALID_INTENTS = [
    "grade_query",         # Consulta de notas
    "attendance_query",    # Consulta de frequência
    "schedule_query",      # Consulta de horários
    "boleto_query",        # Consulta/2ª via de boleto
    "enrollment_query",    # Situação de matrícula
    "payslip_query",       # Consulta de holerite
    "vacation_query",      # Saldo de férias
    "time_record_query",   # Registro de ponto
    "hr_request",          # Solicitação de RH (atestado, declaração)
    "faq",                 # Pergunta geral / FAQ
    "human_handoff",       # Pedido de atendente humano
    "greeting",            # Saudação inicial
    "verification",        # Verificação de identidade (RA/matrícula)
    "unknown",             # Intenção não reconhecida
]

CLASSIFIER_SYSTEM_PROMPT = """Você é um classificador de intenções para um sistema de atendimento universitário.
Classifique a mensagem do usuário em EXATAMENTE uma das seguintes intenções:

grade_query, attendance_query, schedule_query, boleto_query, enrollment_query,
payslip_query, vacation_query, time_record_query, hr_request, faq, human_handoff, greeting, verification, unknown

Responda APENAS com um JSON no formato: {"intent": "nome_da_intencao", "entities": {}}
Para entities, extraia dados relevantes como: subject (matéria), period (período), month (mês), type (tipo).
Não adicione explicações."""


async def classify_intent(message: str, context_type: Optional[str] = None) -> dict:
    """
    Classifica a intenção da mensagem usando Claude.
    Retorna: {"intent": str, "entities": dict}
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    context_hint = ""
    if context_type == "student":
        context_hint = "\nContexto: usuário é um aluno."
    elif context_type == "employee":
        context_hint = "\nContexto: usuário é um funcionário/RH."

    try:
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_CLASSIFIER_MAX_TOKENS,
            system=CLASSIFIER_SYSTEM_PROMPT + context_hint,
            messages=[{"role": "user", "content": message}],
        )

        raw = response.content[0].text.strip()

        # Extrai JSON da resposta
        if "{" in raw:
            json_str = raw[raw.index("{") : raw.rindex("}") + 1]
            result = json.loads(json_str)
            intent = result.get("intent", "unknown")
            if intent not in VALID_INTENTS:
                intent = "unknown"
            return {"intent": intent, "entities": result.get("entities", {})}

    except Exception as e:
        logger.warning("Erro ao classificar intenção: %s", e)

    return {"intent": "unknown", "entities": {}}
