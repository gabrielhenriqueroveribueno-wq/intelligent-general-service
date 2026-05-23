# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Análise de sentimento das mensagens de WhatsApp — abordagem híbrida:
1. Classificação rápida por palavras-chave em PT-BR (sem custo de AI)
2. Pontuação entre -1.0 (muito negativo) e +1.0 (muito positivo)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Sentiment = Literal["positive", "neutral", "negative"]

_NEGATIVE_KEYWORDS: list[tuple[str, float]] = [
    # Intenção de abandono / evasão
    ("cancelar matrícula", -0.9),
    ("trancar curso", -0.9),
    ("largar o curso", -0.9),
    ("desistir", -0.85),
    ("abandonar", -0.85),
    ("vou largar", -0.8),
    ("sair da faculdade", -0.8),
    ("não quero mais", -0.7),
    # Frustração / insatisfação
    ("absurdo", -0.8),
    ("ridículo", -0.8),
    ("péssimo", -0.8),
    ("horrível", -0.8),
    ("incompetência", -0.8),
    ("incompetente", -0.75),
    ("indignado", -0.75),
    ("revoltado", -0.75),
    ("decepcionado", -0.7),
    ("decepção", -0.7),
    ("uma vergonha", -0.75),
    ("que vergonha", -0.75),
    ("problema", -0.4),
    ("erro", -0.35),
    ("não funciona", -0.5),
    ("não resolve", -0.5),
    ("demora demais", -0.5),
    ("nunca resolve", -0.6),
    ("sempre errado", -0.6),
    ("pessima", -0.8),
    ("nunca mais", -0.7),
    ("reclamação", -0.55),
    ("reclamar", -0.5),
    ("raiva", -0.7),
    ("odeio", -0.8),
    ("horroro", -0.8),
    ("pior", -0.55),
    ("insatisfeito", -0.65),
    ("triste", -0.4),
    ("preocupado", -0.3),
    ("dificuldade financeira", -0.5),
    ("sem dinheiro", -0.4),
    ("não consigo pagar", -0.55),
    ("não vou conseguir pagar", -0.65),
    ("boleto atrasado", -0.4),
    ("fui reprovado", -0.5),
    ("reprovei", -0.5),
    ("zerando", -0.5),
    ("nota baixa", -0.4),
    ("muita falta", -0.4),
    ("muitas faltas", -0.4),
]

_POSITIVE_KEYWORDS: list[tuple[str, float]] = [
    ("obrigado", 0.4),
    ("obrigada", 0.4),
    ("muito obrigado", 0.6),
    ("muito obrigada", 0.6),
    ("valeu", 0.35),
    ("grato", 0.5),
    ("grata", 0.5),
    ("excelente", 0.75),
    ("ótimo", 0.7),
    ("ótima", 0.7),
    ("perfeito", 0.7),
    ("satisfeito", 0.65),
    ("maravilha", 0.75),
    ("adorei", 0.75),
    ("funcionou", 0.5),
    ("resolveu", 0.55),
    ("resolvido", 0.55),
    ("consegui", 0.4),
    ("feliz", 0.6),
    ("animado", 0.55),
    ("animada", 0.55),
    ("muito bom", 0.65),
    ("muito boa", 0.65),
    ("melhorou", 0.4),
    ("nota boa", 0.45),
    ("aprovei", 0.6),
    ("passei", 0.6),
    ("nota alta", 0.5),
    ("tudo certo", 0.45),
    ("tudo ok", 0.45),
]


@dataclass
class SentimentResult:
    label: Sentiment
    score: float  # -1.0 a +1.0
    confidence: float  # 0.0 a 1.0


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def analyze(text: str) -> SentimentResult:
    """Classifica o sentimento de uma mensagem em PT-BR."""
    if not text or not text.strip():
        return SentimentResult(label="neutral", score=0.0, confidence=0.5)

    normalized = _normalize(text)
    total_score = 0.0
    hits = 0

    for kw, weight in _NEGATIVE_KEYWORDS:
        if kw in normalized:
            total_score += weight
            hits += 1

    for kw, weight in _POSITIVE_KEYWORDS:
        if kw in normalized:
            total_score += weight
            hits += 1

    if hits == 0:
        return SentimentResult(label="neutral", score=0.0, confidence=0.5)

    avg_score = max(-1.0, min(1.0, total_score / hits))
    confidence = min(1.0, 0.5 + abs(avg_score) * 0.5)

    if avg_score <= -0.25:
        label: Sentiment = "negative"
    elif avg_score >= 0.25:
        label = "positive"
    else:
        label = "neutral"

    return SentimentResult(label=label, score=round(avg_score, 3), confidence=round(confidence, 3))


def is_evasion_signal(text: str) -> bool:
    """Detecta se a mensagem contém sinal explícito de intenção de abandono."""
    normalized = _normalize(text)
    evasion_phrases = [
        "cancelar matrícula",
        "trancar curso",
        "largar o curso",
        "desistir",
        "abandonar o curso",
        "sair da faculdade",
        "vou largar",
        "não quero mais estudar",
        "trancamento",
    ]
    return any(phrase in normalized for phrase in evasion_phrases)
