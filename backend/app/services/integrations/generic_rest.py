"""
Integrador generico via REST + JSON.

Funciona com qualquer sistema academico que exponha endpoints HTTP retornando
JSON. O usuario configura no painel:

- base_url: URL do sistema
- auth: {"type": "bearer" | "basic" | "header", ...}
- students_endpoint: path relativo (ex: "/api/students")
- field_mapping: {nosso_campo: caminho_no_json} via JSONPath simples

Exemplo de config:
{
  "base_url": "https://portal.minhaescola.com.br",
  "students_endpoint": "/api/students",
  "students_root_path": "data",
  "students_pagination": {"type": "offset", "param": "offset", "limit": 100},
  "field_mapping": {
    "registration_number": "matricula",
    "full_name": "nome_completo",
    "course": "curso.nome",
    "semester": "semestre_atual",
    "email": "contato.email",
    "phone": "contato.telefone"
  }
}
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

import httpx

from app.services.integrations.base import (
    SyncResult,
    upsert_employee,
    upsert_student,
)

logger = logging.getLogger(__name__)


HTTP_TIMEOUT_SECONDS = 30.0
MAX_PAGES = 200


class GenericRestIntegrator:
    """Integrador HTTP/JSON generico configuravel via JSON."""

    provider_type = "generic_rest"

    def __init__(self, config: dict, credentials: dict):
        self.config = config or {}
        self.credentials = credentials or {}

        self.base_url = (self.config.get("base_url") or "").rstrip("/")
        if not self.base_url:
            raise ValueError("config.base_url eh obrigatorio")

    # ── Auth ────────────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        auth = self.credentials.get("auth") or {}
        auth_type = auth.get("type", "bearer")

        if auth_type == "bearer":
            token = auth.get("token", "")
            if not token:
                return {}
            return {"Authorization": f"Bearer {token}"}

        if auth_type == "header":
            name = auth.get("header_name", "X-Api-Key")
            value = auth.get("header_value", "")
            if not value:
                return {}
            return {name: value}

        if auth_type == "basic":
            import base64

            user = auth.get("username", "")
            pwd = auth.get("password", "")
            raw = f"{user}:{pwd}".encode("utf-8")
            return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}

        return {}

    def _httpx_auth(self) -> Optional[httpx.BasicAuth]:
        auth = self.credentials.get("auth") or {}
        if auth.get("type") == "basic":
            return None  # Ja vai no header
        return None

    # ── HTTP helper ─────────────────────────────────────────────────────────

    async def _fetch_json(self, url: str, params: Optional[dict] = None) -> Any:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            r = await client.get(url, headers=self._auth_headers(), params=params)
            r.raise_for_status()
            return r.json()

    # ── JSONPath simples (apenas dot notation, sem [], filters etc) ─────────

    @staticmethod
    def _resolve_path(obj: Any, path: str) -> Any:
        if not path:
            return obj
        cur = obj
        for part in path.split("."):
            if cur is None:
                return None
            if isinstance(cur, dict):
                cur = cur.get(part)
            elif isinstance(cur, list):
                try:
                    cur = cur[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return cur

    # ── Pagination ──────────────────────────────────────────────────────────

    async def _fetch_all_pages(
        self, endpoint: str, root_path: str, pagination: Optional[dict]
    ) -> list[dict]:
        url = f"{self.base_url}{endpoint}"
        all_items: list[dict] = []

        if not pagination:
            data = await self._fetch_json(url)
            items = self._resolve_path(data, root_path) or []
            return items if isinstance(items, list) else []

        ptype = pagination.get("type", "offset")
        limit = int(pagination.get("limit", 100))

        if ptype == "offset":
            param = pagination.get("param", "offset")
            offset = 0
            for _ in range(MAX_PAGES):
                data = await self._fetch_json(url, params={param: offset, "limit": limit})
                page = self._resolve_path(data, root_path) or []
                if not isinstance(page, list) or not page:
                    break
                all_items.extend(page)
                if len(page) < limit:
                    break
                offset += limit

        elif ptype == "page":
            param = pagination.get("param", "page")
            page_num = 1
            for _ in range(MAX_PAGES):
                data = await self._fetch_json(url, params={param: page_num, "per_page": limit})
                page = self._resolve_path(data, root_path) or []
                if not isinstance(page, list) or not page:
                    break
                all_items.extend(page)
                if len(page) < limit:
                    break
                page_num += 1

        else:
            data = await self._fetch_json(url)
            items = self._resolve_path(data, root_path) or []
            all_items = items if isinstance(items, list) else []

        return all_items

    # ── Test connection ─────────────────────────────────────────────────────

    async def test_connection(self) -> tuple[bool, str]:
        endpoint = self.config.get("test_endpoint") or self.config.get("students_endpoint", "/")
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url, headers=self._auth_headers())
            if r.status_code in (200, 201):
                return True, f"OK ({r.status_code})"
            if r.status_code == 401:
                return False, "Credenciais invalidas (401)"
            if r.status_code == 403:
                return False, "Acesso negado (403)"
            if r.status_code == 404:
                return False, f"Endpoint nao encontrado: {endpoint}"
            return False, f"HTTP {r.status_code}"
        except httpx.TimeoutException:
            return False, "Timeout — servidor nao respondeu em 10s"
        except httpx.ConnectError as exc:
            return False, f"Falha de conexao: {exc}"
        except Exception as exc:
            return False, f"Erro: {exc}"

    # ── Sync students ───────────────────────────────────────────────────────

    async def sync_students(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        endpoint = self.config.get("students_endpoint")
        if not endpoint:
            result.warnings.append("students_endpoint nao configurado — pulando alunos")
            return result

        mapping = self.config.get("field_mapping", {})
        root_path = self.config.get("students_root_path", "")
        pagination = self.config.get("students_pagination")

        try:
            items = await self._fetch_all_pages(endpoint, root_path, pagination)
        except Exception as exc:
            result.success = False
            result.add_error(f"Falha buscando alunos: {exc}")
            return result

        for item in items:
            try:
                ra = str(
                    self._resolve_path(item, mapping.get("registration_number", "matricula")) or ""
                ).strip()
                name = str(self._resolve_path(item, mapping.get("full_name", "nome")) or "").strip()
                if not ra or not name:
                    continue

                semester_raw = self._resolve_path(item, mapping.get("semester", "semestre"))
                semester = int(semester_raw) if semester_raw else None

                created, _ = await upsert_student(
                    db,
                    tenant_id,
                    registration_number=ra,
                    full_name=name,
                    course=str(self._resolve_path(item, mapping.get("course", "curso")) or "")
                    or None,
                    semester=semester,
                    enrollment_status=str(
                        self._resolve_path(item, mapping.get("enrollment_status", "status"))
                        or "active"
                    ),
                    email=str(self._resolve_path(item, mapping.get("email", "email")) or "")
                    or None,
                    phone=str(self._resolve_path(item, mapping.get("phone", "telefone")) or "")
                    or None,
                )
                if created:
                    result.students_created += 1
                else:
                    result.students_updated += 1
                result.records_synced += 1
            except Exception as exc:
                result.add_error(f"Erro em aluno {item}: {exc}")

        await db.flush()
        logger.info(
            "GenericREST sync_students: tenant=%s criados=%d atualizados=%d erros=%d",
            tenant_id,
            result.students_created,
            result.students_updated,
            len(result.errors),
        )
        return result

    # ── Sync employees ──────────────────────────────────────────────────────

    async def sync_employees(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        endpoint = self.config.get("employees_endpoint")
        if not endpoint:
            return result

        mapping = self.config.get("employee_field_mapping") or self.config.get("field_mapping", {})
        root_path = self.config.get("employees_root_path", "")
        pagination = self.config.get("employees_pagination")

        try:
            items = await self._fetch_all_pages(endpoint, root_path, pagination)
        except Exception as exc:
            result.success = False
            result.add_error(f"Falha buscando funcionarios: {exc}")
            return result

        for item in items:
            try:
                num = str(
                    self._resolve_path(item, mapping.get("employee_number", "matricula")) or ""
                ).strip()
                name = str(self._resolve_path(item, mapping.get("full_name", "nome")) or "").strip()
                if not num or not name:
                    continue

                created, _ = await upsert_employee(
                    db,
                    tenant_id,
                    employee_number=num,
                    full_name=name,
                    department=str(
                        self._resolve_path(item, mapping.get("department", "departamento")) or ""
                    )
                    or None,
                    position=str(self._resolve_path(item, mapping.get("position", "cargo")) or "")
                    or None,
                    status=str(
                        self._resolve_path(item, mapping.get("status", "status")) or "active"
                    ),
                    email=str(self._resolve_path(item, mapping.get("email", "email")) or "")
                    or None,
                    phone=str(self._resolve_path(item, mapping.get("phone", "telefone")) or "")
                    or None,
                )
                if created:
                    result.employees_created += 1
                else:
                    result.employees_updated += 1
                result.records_synced += 1
            except Exception as exc:
                result.add_error(f"Erro em funcionario {item}: {exc}")

        await db.flush()
        return result

    # ── Optional methods (no-op por default) ────────────────────────────────

    async def sync_grades(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        result.warnings.append("sync_grades nao implementado para Generic REST")
        return result

    async def sync_boletos(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        result.warnings.append("sync_boletos nao implementado para Generic REST")
        return result

    async def sync_all(self, db, tenant_id: uuid.UUID) -> SyncResult:
        start = time.perf_counter()
        s = await self.sync_students(db, tenant_id)
        e = await self.sync_employees(db, tenant_id)
        merged = s.merge(e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "GenericREST sync_all completo em %dms: tenant=%s registros=%d erros=%d",
            elapsed_ms,
            tenant_id,
            merged.records_synced,
            len(merged.errors),
        )
        return merged
