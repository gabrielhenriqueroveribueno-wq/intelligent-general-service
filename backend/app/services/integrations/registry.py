"""
Registry/factory para instanciar o integrador correto pelo tipo.

Tambem expoe metadados (label, descricao, campos esperados) para o frontend
montar o formulario de configuracao dinamico.
"""

from __future__ import annotations

import json
import logging

from app.services.integrations.base import AcademicSystemIntegrator
from app.services.integrations.generic_rest import GenericRestIntegrator
from app.services.integrations.sophia import SophiaIntegrator
from app.services.integrations.totvs import TotvsIntegrator
from app.utils.encryption import decrypt

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Provider catalog
# ══════════════════════════════════════════════════════════════════════════════


PROVIDER_CATALOG: list[dict] = [
    {
        "type": "sophia",
        "label": "Sophia (Prima)",
        "description": "ERP educacional usado em faculdades de medio/grande porte",
        "config_fields": [
            {
                "name": "base_url",
                "label": "URL base",
                "type": "url",
                "required": True,
                "placeholder": "https://escola.sophia.com.br",
            },
            {
                "name": "tenant_code",
                "label": "Codigo da instituicao",
                "type": "text",
                "required": False,
            },
        ],
        "credential_fields": [
            {"name": "auth.token", "label": "API Token", "type": "password", "required": True},
        ],
    },
    {
        "type": "totvs",
        "label": "TOTVS RM Educacional",
        "description": "Modulo educacional do TOTVS RM",
        "config_fields": [
            {
                "name": "base_url",
                "label": "URL base",
                "type": "url",
                "required": True,
                "placeholder": "https://escola.totvs.com.br/api/framework/v1",
            },
            {
                "name": "coligada",
                "label": "Codigo da Coligada (CODCOLIGADA)",
                "type": "text",
                "required": True,
                "placeholder": "1",
            },
        ],
        "credential_fields": [
            {"name": "username", "label": "Usuario RM", "type": "text", "required": True},
            {"name": "password", "label": "Senha RM", "type": "password", "required": True},
        ],
    },
    {
        "type": "generic_rest",
        "label": "REST Generico (qualquer sistema com API JSON)",
        "description": "Configure URL, autenticacao e mapeamento de campos para "
        "integrar qualquer sistema que exponha REST + JSON",
        "config_fields": [
            {"name": "base_url", "label": "URL base", "type": "url", "required": True},
            {
                "name": "students_endpoint",
                "label": "Endpoint de alunos",
                "type": "text",
                "required": False,
                "placeholder": "/api/students",
            },
            {
                "name": "employees_endpoint",
                "label": "Endpoint de funcionarios",
                "type": "text",
                "required": False,
                "placeholder": "/api/employees",
            },
        ],
        "credential_fields": [
            {
                "name": "auth.type",
                "label": "Tipo de autenticacao",
                "type": "select",
                "options": ["bearer", "basic", "header"],
                "default": "bearer",
            },
            {
                "name": "auth.token",
                "label": "Token (bearer)",
                "type": "password",
                "required": False,
            },
            {
                "name": "auth.username",
                "label": "Usuario (basic)",
                "type": "text",
                "required": False,
            },
            {
                "name": "auth.password",
                "label": "Senha (basic)",
                "type": "password",
                "required": False,
            },
            {
                "name": "auth.header_name",
                "label": "Nome do header (custom)",
                "type": "text",
                "required": False,
                "placeholder": "X-Api-Key",
            },
            {
                "name": "auth.header_value",
                "label": "Valor do header (custom)",
                "type": "password",
                "required": False,
            },
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Factory
# ══════════════════════════════════════════════════════════════════════════════


_INTEGRATOR_CLASSES: dict[str, type] = {
    "sophia": SophiaIntegrator,
    "totvs": TotvsIntegrator,
    "generic_rest": GenericRestIntegrator,
}


def get_integrator(
    provider_type: str,
    config: dict,
    credentials: dict,
) -> AcademicSystemIntegrator:
    """
    Instancia o integrador correto pelo tipo.

    Args:
        provider_type: 'sophia' | 'totvs' | 'generic_rest'
        config: dict com configuracao publica (URLs, IDs)
        credentials: dict com credenciais (ja descriptografadas)

    Raises:
        ValueError: se tipo desconhecido
    """
    cls = _INTEGRATOR_CLASSES.get(provider_type)
    if cls is None:
        raise ValueError(
            f"Provider '{provider_type}' nao suportado. "
            f"Suportados: {list(_INTEGRATOR_CLASSES.keys())}"
        )
    return cls(config=config, credentials=credentials)


def decrypt_credentials(encrypted: str | None) -> dict:
    """Descriptografa o JSON de credenciais armazenado no banco."""
    if not encrypted:
        return {}
    plain = decrypt(encrypted)
    if not plain:
        logger.error("Falha ao descriptografar credenciais — verificar ENCRYPTION_KEY")
        return {}
    try:
        return json.loads(plain)
    except json.JSONDecodeError:
        logger.error("Credenciais armazenadas nao sao JSON valido")
        return {}


def encrypt_credentials(credentials: dict) -> str:
    """Serializa e criptografa o dict de credenciais."""
    from app.utils.encryption import encrypt

    return encrypt(json.dumps(credentials, ensure_ascii=False))
