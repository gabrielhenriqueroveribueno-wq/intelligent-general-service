# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Integrador para o sistema academico Sophia (Prima Tecnologia).

Documentacao da API: https://docs.sophia.com.br/api (formato real depende
do contrato com a Prima — endpoints comuns usam autenticacao via token e
respostas JSON).

Implementacao usa httpx com auth Bearer. As estruturas de campo sao
baseadas nos endpoints publicos documentados; cada instalacao do Sophia
pode ter campos customizados que podem ser ajustados via field_mapping
no config (mesmo padrao do GenericRestIntegrator).

Config esperada:
{
  "base_url": "https://anchieta.sophia.com.br",
  "tenant_code": "ANCHIETA",
  "field_mapping": { ... opcional, override dos defaults ... }
}

Credentials esperadas:
{
  "auth": {"type": "bearer", "token": "<api_token>"},
  "username": "...",   # caso a API exija usuario+senha em vez de token
  "password": "..."
}
"""

from __future__ import annotations

import logging
import time
import uuid

import httpx

from app.services.integrations.base import (
    SyncResult,
    upsert_employee,
    upsert_student,
)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS = 30.0


SOPHIA_DEFAULT_MAPPING = {
    "registration_number": "matricula",
    "full_name": "nome",
    "course": "curso.descricao",
    "semester": "periodo_atual",
    "enrollment_status": "situacao",
    "email": "email",
    "phone": "celular",
}


class SophiaIntegrator:
    """Adapter para a API do Sophia (Prima Tecnologia)."""

    provider_type = "sophia"

    def __init__(self, config: dict, credentials: dict):
        self.config = config or {}
        self.credentials = credentials or {}

        self.base_url = (self.config.get("base_url") or "").rstrip("/")
        if not self.base_url:
            raise ValueError("config.base_url eh obrigatorio (ex: https://escola.sophia.com.br)")

        self.tenant_code = self.config.get("tenant_code", "")
        self.mapping = {**SOPHIA_DEFAULT_MAPPING, **(self.config.get("field_mapping") or {})}

    # ── Auth ────────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        auth = self.credentials.get("auth") or {}
        token = auth.get("token") or self.credentials.get("token") or ""
        if not token:
            return {"Accept": "application/json"}
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    @staticmethod
    def _resolve(obj, path: str):
        if not path:
            return obj
        cur = obj
        for part in path.split("."):
            if cur is None:
                return None
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur

    # ── Test connection ─────────────────────────────────────────────────────

    async def test_connection(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Endpoint /alunos eh comum; ajustar se necessario via test_endpoint
                endpoint = self.config.get("test_endpoint", "/alunos?limit=1")
                r = await client.get(f"{self.base_url}{endpoint}", headers=self._headers())
            if r.status_code in (200, 201):
                return True, f"OK (Sophia respondeu {r.status_code})"
            if r.status_code == 401:
                return False, "Token Sophia invalido ou expirado"
            if r.status_code == 403:
                return False, "Sem permissao para acessar Sophia"
            return False, f"Sophia retornou HTTP {r.status_code}"
        except httpx.TimeoutException:
            return False, "Timeout — Sophia nao respondeu em 10s"
        except Exception as exc:
            return False, f"Erro: {exc}"

    # ── Sync students ───────────────────────────────────────────────────────

    async def sync_students(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        endpoint = self.config.get("students_endpoint", "/alunos")

        # Sophia tipicamente pagina com offset/limit
        all_items: list[dict] = []
        offset = 0
        limit = 100

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                for _ in range(200):
                    r = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=self._headers(),
                        params={"offset": offset, "limit": limit},
                    )
                    r.raise_for_status()
                    data = r.json()

                    items = (
                        data
                        if isinstance(data, list)
                        else data.get("data") or data.get("alunos") or []
                    )
                    if not items:
                        break
                    all_items.extend(items)
                    if len(items) < limit:
                        break
                    offset += limit
        except httpx.HTTPError as exc:
            result.success = False
            result.add_error(f"Sophia HTTP error: {exc}")
            return result

        for item in all_items:
            try:
                ra = str(self._resolve(item, self.mapping["registration_number"]) or "").strip()
                name = str(self._resolve(item, self.mapping["full_name"]) or "").strip()
                if not ra or not name:
                    continue

                semester_raw = self._resolve(item, self.mapping["semester"])
                semester = int(semester_raw) if semester_raw else None

                situacao = str(self._resolve(item, self.mapping["enrollment_status"]) or "").lower()
                status_map = {
                    "ativa": "active",
                    "ativo": "active",
                    "trancada": "locked",
                    "trancado": "locked",
                    "formada": "graduated",
                    "formado": "graduated",
                    "cancelada": "dropped",
                    "cancelado": "dropped",
                }
                enrollment_status = status_map.get(situacao, "active")

                created, _ = await upsert_student(
                    db,
                    tenant_id,
                    registration_number=ra,
                    full_name=name,
                    course=str(self._resolve(item, self.mapping["course"]) or "") or None,
                    semester=semester,
                    enrollment_status=enrollment_status,
                    email=str(self._resolve(item, self.mapping["email"]) or "") or None,
                    phone=str(self._resolve(item, self.mapping["phone"]) or "") or None,
                )
                if created:
                    result.students_created += 1
                else:
                    result.students_updated += 1
                result.records_synced += 1
            except Exception as exc:
                result.add_error(f"Erro processando aluno: {exc}")

        await db.flush()
        return result

    # ── Sync employees / grades / boletos ───────────────────────────────────

    async def sync_employees(self, db, tenant_id: uuid.UUID) -> SyncResult:
        """Sophia tem modulo de RH separado — aqui um stub que pode ser
        ativado se o cliente contratar o modulo."""
        result = SyncResult(success=True)
        endpoint = self.config.get("employees_endpoint")
        if not endpoint:
            result.warnings.append("Modulo RH do Sophia nao configurado — pulando funcionarios")
            return result

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                r = await client.get(f"{self.base_url}{endpoint}", headers=self._headers())
                r.raise_for_status()
                items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        except httpx.HTTPError as exc:
            result.success = False
            result.add_error(f"Sophia HTTP error (funcionarios): {exc}")
            return result

        for item in items:
            try:
                num = str(item.get("matricula") or "").strip()
                name = str(item.get("nome") or "").strip()
                if not num or not name:
                    continue
                created, _ = await upsert_employee(
                    db,
                    tenant_id,
                    employee_number=num,
                    full_name=name,
                    department=item.get("departamento"),
                    position=item.get("cargo"),
                    email=item.get("email"),
                    phone=item.get("celular"),
                )
                if created:
                    result.employees_created += 1
                else:
                    result.employees_updated += 1
                result.records_synced += 1
            except Exception as exc:
                result.add_error(f"Erro processando funcionario: {exc}")

        await db.flush()
        return result

    async def sync_grades(self, db, tenant_id: uuid.UUID) -> SyncResult:
        """Sincroniza notas via /notas?aluno=RA — implementacao futura."""
        result = SyncResult(success=True)
        result.warnings.append(
            "sync_grades requer endpoint /notas configurado e politica de "
            "sincronizacao por aluno (lazy on-demand vs batch periodico). "
            "Recomenda-se buscar notas sob demanda no momento da pergunta do aluno."
        )
        return result

    async def sync_boletos(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        result.warnings.append("sync_boletos nao implementado — usar endpoint financeiro do Sophia")
        return result

    async def sync_all(self, db, tenant_id: uuid.UUID) -> SyncResult:
        start = time.perf_counter()
        s = await self.sync_students(db, tenant_id)
        e = await self.sync_employees(db, tenant_id)
        merged = s.merge(e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "Sophia sync_all em %dms: tenant=%s registros=%d erros=%d",
            elapsed_ms,
            tenant_id,
            merged.records_synced,
            len(merged.errors),
        )
        return merged
