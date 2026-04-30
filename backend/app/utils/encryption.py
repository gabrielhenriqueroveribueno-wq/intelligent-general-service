"""
Utilitario de criptografia simetrica (Fernet) para credenciais e PII.

Usa a chave em settings.ENCRYPTION_KEY (deve ser uma Fernet key valida
em base64 — 32 bytes URL-safe). Em desenvolvimento, falhas no decrypt
retornam None em vez de excecao pra nao quebrar a app.
"""

from __future__ import annotations

import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


_cipher: Optional[Fernet] = None


def _get_cipher() -> Optional[Fernet]:
    global _cipher
    if _cipher is not None:
        return _cipher

    key = settings.ENCRYPTION_KEY
    if not key:
        logger.warning("ENCRYPTION_KEY nao configurada — campos sensiveis nao serao criptografados")
        return None

    try:
        _cipher = Fernet(key.encode() if isinstance(key, str) else key)
        return _cipher
    except (ValueError, TypeError) as exc:
        logger.error("ENCRYPTION_KEY invalida: %s", exc)
        return None


def encrypt(plaintext: str) -> str:
    """
    Criptografa string. Se ENCRYPTION_KEY nao configurada, retorna o texto
    com prefixo 'plain:' (so para dev — NUNCA usar em prod sem chave).
    """
    if not plaintext:
        return ""

    cipher = _get_cipher()
    if cipher is None:
        return f"plain:{plaintext}"

    token = cipher.encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(ciphertext: str) -> Optional[str]:
    """
    Descriptografa string. Retorna None se falhar (chave errada, texto
    corrompido, etc.). Aceita o prefixo 'plain:' para fallback de dev.
    """
    if not ciphertext:
        return None

    if ciphertext.startswith("plain:"):
        return ciphertext[len("plain:"):]

    cipher = _get_cipher()
    if cipher is None:
        return None

    try:
        return cipher.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        logger.error("Falha ao descriptografar: %s", exc)
        return None


def is_encrypted(value: str) -> bool:
    """Heuristica: tokens Fernet comecam com 'gAAAAAB' apos base64 decode."""
    if not value or value.startswith("plain:"):
        return False
    return value.startswith("gAAAAAB") or len(value) > 60
