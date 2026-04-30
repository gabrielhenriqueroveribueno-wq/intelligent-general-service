"""
Testes dos utilitarios de seguranca: hashing de senha e JWT.

Bugs aqui = vulnerabilidade direta. Testar com cuidado.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

# ══════════════════════════════════════════════════════════════════════════════
# Password hashing
# ══════════════════════════════════════════════════════════════════════════════


def test_hash_password_returns_different_hash_for_same_input():
    """Bcrypt usa salt aleatorio — hashes do mesmo password sao diferentes."""
    h1 = hash_password("MinhaSenha@123")
    h2 = hash_password("MinhaSenha@123")
    assert h1 != h2


def test_hash_password_does_not_include_plain_text():
    plain = "SenhaSecreta@123"
    h = hash_password(plain)
    assert plain not in h


def test_verify_password_correct():
    plain = "Test@12345"
    h = hash_password(plain)
    assert verify_password(plain, h) is True


def test_verify_password_wrong():
    h = hash_password("CertaSenha@123")
    assert verify_password("OutraSenha@123", h) is False


def test_verify_password_empty_string_fails():
    h = hash_password("Test@12345")
    assert verify_password("", h) is False


def test_hash_password_uses_bcrypt():
    """Hash deve comecar com $2a$ ou $2b$ (bcrypt)."""
    h = hash_password("Test@12345")
    assert h.startswith("$2") and "$" in h[1:]


# ══════════════════════════════════════════════════════════════════════════════
# JWT — access token
# ══════════════════════════════════════════════════════════════════════════════


def test_create_and_decode_access_token():
    payload = {"sub": "user-123", "tenant_id": "tenant-abc", "role": "admin"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["tenant_id"] == "tenant-abc"
    assert decoded["role"] == "admin"
    assert decoded["type"] == "access"
    assert "exp" in decoded


def test_decode_access_token_rejects_refresh_token():
    """Tokens de refresh NAO podem passar como access."""
    refresh = create_refresh_token({"sub": "user-123"})
    decoded = decode_access_token(refresh)
    assert decoded is None


def test_decode_refresh_token_rejects_access_token():
    """Tokens de access NAO podem passar como refresh."""
    access = create_access_token({"sub": "user-123"})
    decoded = decode_refresh_token(access)
    assert decoded is None


def test_decode_access_token_invalid_signature():
    """Token assinado com chave errada deve ser rejeitado."""
    payload = {
        "sub": "user-123",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "chave-errada", algorithm=settings.JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_decode_access_token_expired():
    """Token expirado deve ser rejeitado."""
    payload = {
        "sub": "user-123",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_decode_access_token_garbage_returns_none():
    assert decode_access_token("nao-eh-um-jwt") is None
    assert decode_access_token("") is None
    assert decode_access_token("a.b.c") is None


def test_access_token_expires_in_configured_window():
    """Access token deve ter exp aproximadamente igual ao configurado."""
    token = create_access_token({"sub": "user-1"})
    decoded = decode_access_token(token)
    assert decoded is not None
    exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    delta = abs((exp - expected).total_seconds())
    assert delta < 5  # tolerancia de 5s


def test_refresh_token_lasts_longer_than_access():
    access = create_access_token({"sub": "u"})
    refresh = create_refresh_token({"sub": "u"})

    a_dec = decode_access_token(access)
    r_dec = decode_refresh_token(refresh)
    assert a_dec is not None and r_dec is not None
    assert r_dec["exp"] > a_dec["exp"]
