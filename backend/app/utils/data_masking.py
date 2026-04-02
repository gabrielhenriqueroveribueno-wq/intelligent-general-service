"""
Mascaramento de dados sensíveis (PII) para conformidade LGPD.

Identifica e mascara CPF, e-mail, telefone e cartão de crédito em textos livres.
Usado automaticamente no salvamento de mensagens do WhatsApp.
"""

import re
from typing import Optional

# ── Padrões Regex ────────────────────────────────────────────────────────────

# CPF: 123.456.789-00 ou 12345678900
_CPF_PATTERN = re.compile(r"\b(\d{3})[.\s]?(\d{3})[.\s]?(\d{3})[-.\s]?(\d{2})\b")

# E-mail: user@domain.com
_EMAIL_PATTERN = re.compile(r"\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b")

# Telefone BR: +55 11 91234-5678, (11) 91234-5678, 11912345678, etc.
_PHONE_PATTERN = re.compile(
    r"(?:\+55\s?)?" r"(?:\(?\d{2}\)?\s?)" r"(?:9\s?\d{4}[-.\s]?\d{4}|\d{4}[-.\s]?\d{4})\b"
)

# Cartão de crédito: 4 grupos de 4 dígitos (com ou sem separadores)
_CARD_PATTERN = re.compile(r"\b(\d{4})[-.\s]?(\d{4})[-.\s]?(\d{4})[-.\s]?(\d{4})\b")

# RG: 12.345.678-9 ou 123456789
_RG_PATTERN = re.compile(r"\b(\d{2})[.]?(\d{3})[.]?(\d{3})[-]?(\d{1})\b")


def mask_cpf(text: str) -> str:
    """123.456.789-00 → ***.456.789-**"""

    def _replace(m: re.Match) -> str:
        return f"***.{m.group(2)}.{m.group(3)}-**"

    return _CPF_PATTERN.sub(_replace, text)


def mask_email(text: str) -> str:
    """usuario@dominio.com → u***o@dominio.com"""

    def _replace(m: re.Match) -> str:
        local = m.group(1)
        domain = m.group(2)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"

    return _EMAIL_PATTERN.sub(_replace, text)


def mask_phone(text: str) -> str:
    """(11) 91234-5678 → (11) 9****-5678"""

    def _replace(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        # Mantém DDD + primeiro dígito + últimos 4, mascara o meio
        if len(digits) >= 10:
            # Remove +55 se presente
            if digits.startswith("55") and len(digits) >= 12:
                digits = digits[2:]
            ddd = digits[:2]
            last4 = digits[-4:]
            mid_len = len(digits) - 2 - 4
            return f"({ddd}) {'*' * mid_len}-{last4}"
        return m.group()

    return _PHONE_PATTERN.sub(_replace, text)


def mask_credit_card(text: str) -> str:
    """4539 1234 5678 9012 → 4539 **** **** 9012"""

    def _replace(m: re.Match) -> str:
        return f"{m.group(1)} **** **** {m.group(4)}"

    return _CARD_PATTERN.sub(_replace, text)


def mask_pii(text: Optional[str]) -> Optional[str]:
    """Aplica todas as máscaras de PII em sequência.

    Ordem importa: cartão antes de CPF para evitar conflitos de padrão.
    """
    if not text:
        return text

    result = text
    result = mask_credit_card(result)
    result = mask_cpf(result)
    result = mask_email(result)
    result = mask_phone(result)
    return result
