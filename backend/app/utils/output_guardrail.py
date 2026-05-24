# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Output guardrail para respostas da Billie.

A Billie NUNCA deve emitir CPF completo, cartão de crédito ou email/telefone
de outras pessoas. Mesmo com tenant_id correto nos dados, um LLM pode
alucinar dados de outros usuários. Este módulo é a última linha de defesa
antes de enviar a resposta ao WhatsApp.

Uso:
    issues = audit_llm_output(response_text)
    if issues:
        # bloqueia ou substitui por mensagem genérica
        ...
"""

from __future__ import annotations

import re

# CPF completo (qualquer formato): 123.456.789-00 ou 12345678900
_CPF_PATTERN = re.compile(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}\b")

# Cartão de crédito (4 grupos de 4 dígitos)
_CARD_PATTERN = re.compile(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b")

# Telefone BR com DDD + 9 dígitos
_PHONE_PATTERN = re.compile(r"\b(?:\+55\s?)?\(?\d{2}\)?[\s.-]?9\s?\d{4}[\s.-]?\d{4}\b")


# Resposta de fallback quando guardrail detecta vazamento potencial.
SAFE_FALLBACK_REPLY = (
    "Tive um problema pra processar essa resposta agora. "
    "Pode reformular a pergunta? Se for sobre seus dados, te ajudo na sequência."
)


def audit_llm_output(text: str) -> list[str]:
    """Retorna lista de issues detectados na resposta do LLM.

    Lista vazia = resposta segura para envio.
    Qualquer item na lista = bloqueio recomendado.
    """
    if not text:
        return []

    issues: list[str] = []

    if _CPF_PATTERN.search(text):
        issues.append("cpf_in_response")

    if _CARD_PATTERN.search(text):
        issues.append("card_in_response")

    # Telefones em mensagens são raros e podem ser número da própria instituição
    # (suporte, secretaria). Aceitar até 1 ocorrência, bloquear se ≥2.
    if len(_PHONE_PATTERN.findall(text)) >= 2:
        issues.append("multiple_phones_in_response")

    return issues
