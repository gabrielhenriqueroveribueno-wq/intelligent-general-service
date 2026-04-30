"""
Fallback offline para quando todos os providers de IA falham.

Estratégia em camadas:
1. Busca direta na Knowledge Base por palavras-chave
2. Templates de resposta para intents comuns (notas, boletos, faltas, horários)
3. Mensagem genérica de degradação com orientação pro humano

NUNCA levanta exceção — sempre retorna algo pro usuário.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Response dataclass — mesma shape de AIResponse
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class FallbackResponse:
    text: str
    tokens_used: int = 0
    provider_used: str = "offline_fallback"


# ══════════════════════════════════════════════════════════════════════════════
# Keyword → template mapping
# ══════════════════════════════════════════════════════════════════════════════


INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "grade_query": ("nota", "notas", "boletim", "media", "prova"),
    "attendance_query": ("falta", "faltas", "frequencia", "presenca", "presença", "frequência"),
    "boleto_query": ("boleto", "mensalidade", "pagamento", "pagar", "segunda via", "2a via"),
    "schedule_query": ("horario", "horário", "aula", "biblioteca", "secretaria"),
    "payslip_query": ("holerite", "contracheque", "salario", "salário", "pagamento funcionario"),
    "vacation_query": ("ferias", "férias"),
    "handoff": ("atendente", "humano", "pessoa", "falar com"),
    "greeting": ("oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"),
    "farewell": ("tchau", "obrigado", "obrigada", "valeu", "ate mais", "até mais"),
}


INTENT_TEMPLATES: dict[str, str] = {
    "grade_query": (
        "Oi! 🙂 No momento nosso sistema de IA tá meio instável, então não consigo puxar "
        "suas notas agora. Mas tenta de novo em alguns minutos que deve voltar. "
        "Se for urgente, liga na secretaria ou acessa o portal do aluno."
    ),
    "attendance_query": (
        "Oi! 🙂 Nosso sistema de IA tá instável agora e não consigo checar sua frequência. "
        "Tenta daqui a pouco. Se for urgente, fala com a secretaria."
    ),
    "boleto_query": (
        "Oi! 🙂 Tô com problema pra acessar o sistema de boletos agora. "
        "Tenta de novo em alguns minutos. Você também pode acessar o portal do aluno "
        "ou passar no financeiro pra pegar sua segunda via."
    ),
    "schedule_query": (
        "Oi! 🙂 Não consigo consultar horários agora. Tenta de novo em alguns minutos "
        "ou liga na recepção."
    ),
    "payslip_query": (
        "Oi! 🙂 Meu sistema tá instável e não consigo gerar seu holerite agora. "
        "Tenta daqui a pouco ou passa no RH."
    ),
    "vacation_query": (
        "Oi! 🙂 Tô com problema pra acessar o sistema de férias. "
        "Tenta novamente em alguns minutos ou fala diretamente com o RH."
    ),
    "handoff": (
        "Entendi! Vou registrar seu pedido de atendimento humano. "
        "Um agente vai te responder assim que possível. [HANDOFF]"
    ),
    "greeting": (
        "Oi! Sou a Billie, do atendimento. 🙂 No momento meu sistema principal tá "
        "passando por uma instabilidade. Me diz o que você precisa que eu tento ajudar "
        "mesmo assim!"
    ),
    "farewell": (
        "Obrigada pelo contato! Qualquer coisa, é só me chamar. 😊"
    ),
}


GENERIC_FALLBACK = (
    "Oi! 🙂 Desculpa, meu sistema de IA tá passando por uma instabilidade agora "
    "e não consigo responder direito. Tenta de novo em alguns minutos. "
    "Se for urgente, liga na secretaria ou pede pra falar com um atendente que "
    "eu transfiro. [HANDOFF]"
)


# ══════════════════════════════════════════════════════════════════════════════
# Intent detection
# ══════════════════════════════════════════════════════════════════════════════


def _detect_intent(message: str) -> Optional[str]:
    """
    Detecta intent por palavras-chave usando word boundaries para evitar
    falsos positivos (ex: 'coisa' nao deve casar com 'oi').
    """
    normalized = message.lower().strip()
    if not normalized:
        return None

    # Tokeniza em palavras (mantendo acentos via \w em UTF-8)
    tokens = set(re.findall(r"\w+", normalized, flags=re.UNICODE))
    # Tambem mantem o texto cru pra casar palavras-chave compostas como "bom dia"
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in normalized:
                    return intent
            elif kw in tokens:
                return intent
    return None


# ══════════════════════════════════════════════════════════════════════════════
# KB search (fallback secundário antes do template)
# ══════════════════════════════════════════════════════════════════════════════


async def _search_kb(
    db: AsyncSession,
    tenant_id: UUID,
    message: str,
    max_results: int = 1,
) -> Optional[str]:
    """Busca na KB por palavras-chave. Retorna o conteúdo do artigo mais relevante."""
    try:
        from app.models.knowledge import KnowledgeArticle
    except ImportError:
        logger.debug("KnowledgeArticle model não disponível")
        return None

    normalized = re.sub(r"[^\w\s]", " ", message.lower()).strip()
    words = [w for w in normalized.split() if len(w) >= 4]
    if not words:
        return None

    try:
        stmt = (
            select(KnowledgeArticle)
            .where(KnowledgeArticle.tenant_id == tenant_id)
            .limit(20)
        )
        result = await db.execute(stmt)
        articles = result.scalars().all()
    except Exception as exc:
        logger.debug("Erro consultando KB: %s", exc)
        return None

    best_score = 0
    best_content: Optional[str] = None
    for article in articles:
        haystack = f"{article.title} {article.content}".lower()
        score = sum(1 for w in words if w in haystack)
        if score > best_score:
            best_score = score
            best_content = article.content

    if best_score >= 1 and best_content:
        return best_content
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════


async def generate_fallback_response(
    user_message: str,
    db: Optional[AsyncSession] = None,
    tenant_id: Optional[UUID] = None,
    contact_name: Optional[str] = None,
) -> FallbackResponse:
    """
    Gera resposta quando todos os providers de IA falharam.

    Ordem:
    1. Intent detection → template
    2. KB search (se db + tenant_id fornecidos)
    3. Mensagem genérica com handoff
    """
    intent = _detect_intent(user_message)
    if intent and intent in INTENT_TEMPLATES:
        text = INTENT_TEMPLATES[intent]
        if contact_name and intent not in ("handoff", "farewell"):
            first_name = contact_name.split()[0]
            text = f"Oi, {first_name}! " + text.removeprefix("Oi! ")
        logger.info("Fallback offline: intent=%s", intent)
        return FallbackResponse(text=text)

    if db and tenant_id:
        kb_content = await _search_kb(db, tenant_id, user_message)
        if kb_content:
            logger.info("Fallback offline: KB match")
            return FallbackResponse(
                text=(
                    "Meu sistema tá instável, mas achei isso na base de conhecimento "
                    "que talvez ajude:\n\n" + kb_content
                )
            )

    logger.info("Fallback offline: resposta genérica")
    return FallbackResponse(text=GENERIC_FALLBACK)


def generate_fallback_response_sync(
    user_message: str,
    contact_name: Optional[str] = None,
) -> FallbackResponse:
    """Versão síncrona (sem KB) — pra contextos onde não dá pra usar async."""
    intent = _detect_intent(user_message)
    if intent and intent in INTENT_TEMPLATES:
        text = INTENT_TEMPLATES[intent]
        if contact_name and intent not in ("handoff", "farewell"):
            first_name = contact_name.split()[0]
            text = f"Oi, {first_name}! " + text.removeprefix("Oi! ")
        return FallbackResponse(text=text)
    return FallbackResponse(text=GENERIC_FALLBACK)
