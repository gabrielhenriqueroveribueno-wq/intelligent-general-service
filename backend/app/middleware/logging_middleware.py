"""
Logging estruturado JSON com correlation_id, tenant_id e mascaramento de PII.

Campos emitidos em cada linha:
  time, level, logger, method, path, status, duration_ms,
  correlation_id, tenant_id, ip, user_agent
"""

import base64
import json
import logging
import re
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("igs.access")

# Regexes PII — aplicados ao path e query string antes de logar
_PII_PATTERNS = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "***CPF***"),  # CPF
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "***EMAIL***"),  # email
    (
        re.compile(r"\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s\-]?)?\d{4,5}[\s\-]?\d{4}\b"),
        "***PHONE***",
    ),  # telefone BR
]


def _mask_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _extract_tenant_id(request: Request) -> str | None:
    """Extrai tenant_id do JWT sem validar assinatura."""
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        parts = auth[7:].split(".")
        if len(parts) != 3:
            return None
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return str(payload.get("tenant_id", ""))
    except Exception:
        return None


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid.uuid4())
        tenant_id = _extract_tenant_id(request)
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        safe_path = _mask_pii(str(request.url.path))
        query = str(request.url.query)
        if query:
            safe_path = f"{safe_path}?{_mask_pii(query)}"

        record = {
            "method": request.method,
            "path": safe_path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "correlation_id": correlation_id,
            "tenant_id": tenant_id or "",
            "ip": request.client.host if request.client else "",
            "ua": request.headers.get("user-agent", "")[:120],
        }

        log_fn = logger.warning if response.status_code >= 500 else logger.info
        log_fn(json.dumps(record, ensure_ascii=False))

        response.headers["X-Correlation-ID"] = correlation_id
        return response
