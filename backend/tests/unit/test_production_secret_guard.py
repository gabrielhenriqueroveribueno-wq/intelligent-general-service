"""Testa o fail-closed de secrets default em producao (app.main._validate_production_secrets)."""

from unittest.mock import patch

import pytest

from app.main import _validate_production_secrets


def _fake_settings(**overrides):
    base = {
        "is_production": True,
        "JWT_SECRET_KEY": "x" * 40,
        "APP_SECRET_KEY": "a-real-app-secret",
        "ENCRYPTION_KEY": "fernet-key",
        "WHATSAPP_APP_SECRET": "meta-secret",
    }
    base.update(overrides)

    class _S:
        pass

    s = _S()
    for k, v in base.items():
        setattr(s, k, v)
    return s


@pytest.mark.unit
def test_passes_with_strong_secrets():
    with patch("app.main.settings", _fake_settings()):
        _validate_production_secrets()  # nao levanta


@pytest.mark.unit
def test_skips_outside_production():
    with patch(
        "app.main.settings",
        _fake_settings(is_production=False, JWT_SECRET_KEY="change-me-jwt-secret"),
    ):
        _validate_production_secrets()  # nao levanta fora de producao


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {"JWT_SECRET_KEY": "change-me-jwt-secret"},
        {"JWT_SECRET_KEY": "short"},
        {"JWT_SECRET_KEY": ""},
        {"APP_SECRET_KEY": "change-me-in-production"},
        {"ENCRYPTION_KEY": ""},
        {"WHATSAPP_APP_SECRET": ""},
    ],
)
def test_fails_closed_on_insecure_config(overrides):
    with patch("app.main.settings", _fake_settings(**overrides)):
        with pytest.raises(RuntimeError):
            _validate_production_secrets()
