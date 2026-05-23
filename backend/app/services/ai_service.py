# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import hashlib
import json
import logging
from typing import Any, Dict, Optional

from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)

_AI_CACHE_TTL = 300  # 5 minutes — short enough to stay fresh, long enough to absorb spikes
_CACHEABLE_INTENTS = {"greeting", "general_query", "kb_query", "faq"}


async def _cache_get(key: str) -> Optional[tuple[str, int]]:
    try:
        import redis.asyncio as aioredis
        from app.config import settings

        client = aioredis.from_url(settings.REDIS_URL.replace("/0", "/5"))
        try:
            raw = await client.get(key)
            if raw:
                data = json.loads(raw)
                return data["text"], data["tokens"]
        finally:
            await client.aclose()
    except Exception:
        pass
    return None


async def _cache_set(key: str, text: str, tokens: int) -> None:
    try:
        import redis.asyncio as aioredis
        from app.config import settings

        client = aioredis.from_url(settings.REDIS_URL.replace("/0", "/5"))
        try:
            await client.setex(key, _AI_CACHE_TTL, json.dumps({"text": text, "tokens": tokens}))
        finally:
            await client.aclose()
    except Exception:
        pass

BOT_SYSTEM_PROMPT = """Você é um assistente virtual universitário chamado {bot_name}.
Você atende alunos e funcionários da instituição via WhatsApp.

REGRAS OBRIGATÓRIAS:
1. Responda SOMENTE com base nos dados fornecidos abaixo. NUNCA invente informações.
2. Se os dados não contiverem a informação solicitada, diga: "Não encontrei essa informação. Por favor, entre em contato com a secretaria."
3. Use linguagem clara, direta e amigável em português brasileiro.
4. Seja conciso - respostas via WhatsApp devem ser curtas.
5. Use emojis moderadamente para deixar a mensagem mais amigável.
6. Se o usuário pedir algo fora do seu escopo, ofereça encaminhar para um atendente humano.
7. Se houver resoluções anteriores similares, use-as como referência para sugerir a melhor solução.

DADOS DISPONÍVEIS:
{data_context}

BASE DE CONHECIMENTO:
{kb_context}

RESOLUÇÕES ANTERIORES SIMILARES:
{similar_resolutions}

HISTÓRICO DA CONVERSA:
{conversation_history}
"""


async def generate_response(
    message: str,
    intent: str,
    data_context: Dict[str, Any],
    kb_articles: list,
    conversation_history: list,
    bot_name: str = "Assistente",
    api_key: Optional[str] = None,
    similar_resolutions: Optional[list] = None,
) -> tuple[str, int]:
    """
    Gera uma resposta inteligente usando o provider de IA configurado.
    Retorna: (resposta, tokens_usados)
    """
    # Formata contexto de dados
    data_str = _format_data_context(intent, data_context)

    # Formata artigos da KB
    kb_str = _format_kb_context(kb_articles)

    # Formata histórico da conversa (últimas 5 mensagens)
    history_str = _format_history(conversation_history[-5:])

    # Formata resoluções similares
    resolutions_str = _format_similar_resolutions(similar_resolutions)

    system = BOT_SYSTEM_PROMPT.format(
        bot_name=bot_name,
        data_context=data_str or "Nenhum dado disponível para esta consulta.",
        kb_context=kb_str or "Nenhum artigo relevante encontrado.",
        similar_resolutions=resolutions_str or "Nenhuma resolução anterior encontrada.",
        conversation_history=history_str or "Início da conversa.",
    )

    cache_key: Optional[str] = None
    if intent in _CACHEABLE_INTENTS:
        fingerprint = hashlib.sha256(f"{system}|{message}".encode()).hexdigest()
        cache_key = f"ai_resp:{fingerprint}"
        cached = await _cache_get(cache_key)
        if cached:
            logger.debug("AI cache hit for intent=%s key=%s", intent, cache_key[:12])
            return cached

    try:
        from app.config import settings

        result = await ai_complete(
            system=system,
            message=message,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            api_key=api_key,
        )
        if cache_key:
            await _cache_set(cache_key, result.text, result.tokens_used)
        return result.text, result.tokens_used

    except Exception as e:
        logger.error("Erro na API de IA: %s", e)
        return (
            "Desculpe, estou com dificuldades técnicas no momento. "
            "Tente novamente em alguns instantes ou fale com um atendente. 🙏",
            0,
        )


def _format_data_context(intent: str, data: Dict[str, Any]) -> str:
    if not data:
        return ""

    lines = []
    if intent == "grade_query" and "grades" in data:
        lines.append("=== NOTAS ===")
        for g in data["grades"]:
            lines.append(
                f"- {g['subject_name']} ({g['academic_period']}): "
                f"{g['grade_type']} = {g.get('grade_value', 'Não lançada')} "
                f"[{g.get('status', '')}]"
            )
    elif intent == "attendance_query" and "attendance" in data:
        lines.append("=== FREQUÊNCIA ===")
        for a in data["attendance"]:
            lines.append(
                f"- {a['subject_name']} ({a['academic_period']}): "
                f"{a['attended']}/{a['total_classes']} aulas "
                f"({a.get('absence_pct', 0):.1f}% faltas)"
            )
    elif intent == "boleto_query" and "boletos" in data:
        lines.append("=== BOLETOS ===")
        for b in data["boletos"]:
            lines.append(
                f"- {b['reference_month']}: R$ {b['amount']:.2f} "
                f"[{b['status']}] Vence: {b.get('due_date', 'N/A')}"
            )
    elif intent == "payslip_query" and "payslips" in data:
        lines.append("=== HOLERITES ===")
        for p in data["payslips"]:
            lines.append(
                f"- {p['reference_month']}: Bruto R$ {p['gross_salary']:.2f} / "
                f"Líquido R$ {p['net_salary']:.2f}"
            )
    elif intent == "vacation_query" and "vacation" in data:
        v = data["vacation"]
        lines.append("=== FÉRIAS ===")
        lines.append(f"- Dias disponíveis: {v.get('remaining_days', 0)}")
        lines.append(f"- Dias usados: {v.get('used_days', 0)}")
        lines.append(f"- Prazo limite: {v.get('deadline_date', 'N/A')}")
    elif intent == "schedule_query" and "schedules" in data:
        lines.append("=== GRADE HORÁRIA ===")
        for s in data["schedules"]:
            lines.append(
                f"- {s['day']}: {s['subject_name']} — "
                f"{s['start_time']}-{s['end_time']} — "
                f"Sala: {s.get('room', 'N/A')} — Prof: {s.get('professor', 'N/A')}"
            )
    elif intent == "time_record_query" and "time_records" in data:
        lines.append("=== REGISTROS DE PONTO ===")
        for r in data["time_records"]:
            lines.append(
                f"- {r['date']}: {r['clock_in']}→{r['clock_out']} "
                f"({r['total_hours']}h) [{r['status']}]"
            )
    elif intent == "hr_request" and "hr_requests" in data:
        lines.append("=== SOLICITAÇÕES RH ===")
        for r in data["hr_requests"]:
            lines.append(f"- {r['type']}: {r.get('description', '')[:100]} [{r['status']}]")
            if r.get("response"):
                lines.append(f"  → Resposta: {r['response'][:150]}")
    elif "student" in data:
        s = data["student"]
        lines.append("=== DADOS DO ALUNO ===")
        lines.append(f"- Nome: {s.get('full_name')}")
        lines.append(f"- RA: {s.get('registration_number')}")
        lines.append(f"- Curso: {s.get('course')}")
        lines.append(f"- Situação: {s.get('enrollment_status')}")
    elif "employee" in data:
        e = data["employee"]
        lines.append("=== DADOS DO FUNCIONÁRIO ===")
        lines.append(f"- Nome: {e.get('full_name')}")
        lines.append(f"- Matrícula: {e.get('employee_number')}")
        lines.append(f"- Departamento: {e.get('department')}")
        lines.append(f"- Cargo: {e.get('position')}")
    else:
        for k, v in data.items():
            lines.append(f"{k}: {v}")

    return "\n".join(lines)


def _format_kb_context(articles: list) -> str:
    if not articles:
        return ""
    lines = []
    for art in articles[:3]:  # Máximo 3 artigos
        lines.append(f"[{art.get('title')}]\n{art.get('content')}")
    return "\n\n".join(lines)


def _format_history(history: list) -> str:
    if not history:
        return ""
    lines = []
    for msg in history:
        role = "Usuário" if msg.get("sender_type") == "user" else "Bot"
        lines.append(f"{role}: {msg.get('content', '')[:200]}")
    return "\n".join(lines)


def _format_similar_resolutions(resolutions: Optional[list]) -> str:
    if not resolutions:
        return ""
    lines = []
    for i, r in enumerate(resolutions[:3], 1):
        score = (
            f" (satisfação: {r.get('satisfaction_score')}/5)" if r.get("satisfaction_score") else ""
        )
        lines.append(
            f"[Resolução {i}]{score}\n"
            f"Problema: {r.get('problem_description', '')[:200]}\n"
            f"Solução: {r.get('resolution_description', '')[:300]}"
        )
    return "\n\n".join(lines)
