# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Integrador para TOTVS RM Educacional via API REST/OData.

A TOTVS expoe APIs via WebApp (REST) ou OData (consultas). A integracao
real exige:
- URL base do RM (ex: https://escola.totvs.com.br/api/framework/v1)
- Usuario + senha do RM ou token de Service User
- Codigo da Coligada (CODCOLIGADA)

Este integrador usa autenticacao Basic via username+password (padrao TOTVS
Framework) e endpoints REST padrao do modulo Educacional.
"""

from __future__ import annotations

import base64
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


TOTVS_DEFAULT_MAPPING = {
    "registration_number": "RA",
    "full_name": "NOME",
    "course": "CURSO",
    "semester": "PERIODOATUAL",
    "enrollment_status": "STATUS",
    "email": "EMAIL",
    "phone": "TELEFONE",
}


class TotvsIntegrator:
    """Adapter para TOTVS RM Educacional."""

    provider_type = "totvs"

    def __init__(self, config: dict, credentials: dict):
        self.config = config or {}
        self.credentials = credentials or {}

        self.base_url = (self.config.get("base_url") or "").rstrip("/")
        if not self.base_url:
            raise ValueError(
                "config.base_url eh obrigatorio (ex: https://escola.totvs.com.br/api/framework/v1)"
            )

        self.coligada = self.config.get("coligada", "1")
        self.mapping = {**TOTVS_DEFAULT_MAPPING, **(self.config.get("field_mapping") or {})}

    # ── Auth ────────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        user = self.credentials.get("username") or ""
        pwd = self.credentials.get("password") or ""
        token = self.credentials.get("token") or ""

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif user and pwd:
            raw = f"{user}:{pwd}".encode("utf-8")
            headers["Authorization"] = f"Basic {base64.b64encode(raw).decode('ascii')}"
        return headers

    @staticmethod
    def _resolve(obj, path: str):
        if not path:
            return obj
        cur = obj
        for part in path.split("."):
            if cur is None:
                return None
            if isinstance(cur, dict):
                cur = cur.get(part) or cur.get(part.upper()) or cur.get(part.lower())
            else:
                return None
        return cur

    # ── Test connection ─────────────────────────────────────────────────────

    async def test_connection(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Endpoint comum de versao do TOTVS Framework
                endpoint = self.config.get("test_endpoint", "/version")
                r = await client.get(f"{self.base_url}{endpoint}", headers=self._headers())
            if r.status_code in (200, 201):
                return True, f"OK (TOTVS respondeu {r.status_code})"
            if r.status_code == 401:
                return False, "Credenciais TOTVS invalidas"
            if r.status_code == 404:
                # Tenta endpoint alternativo
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r2 = await client.get(
                        f"{self.base_url}/educacional/Aluno?$top=1",
                        headers=self._headers(),
                    )
                if r2.status_code == 200:
                    return True, "OK (endpoint educacional acessivel)"
                return False, f"TOTVS HTTP {r2.status_code}"
            return False, f"TOTVS HTTP {r.status_code}"
        except httpx.TimeoutException:
            return False, "Timeout — TOTVS nao respondeu em 10s"
        except Exception as exc:
            return False, f"Erro: {exc}"

    # ── Sync students (OData paginated) ─────────────────────────────────────

    async def sync_students(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        endpoint = self.config.get("students_endpoint", "/educacional/Aluno")

        all_items: list[dict] = []
        skip = 0
        top = 100
        coligada_filter = f"CODCOLIGADA eq {self.coligada}"

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                for _ in range(200):
                    r = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=self._headers(),
                        params={
                            "$filter": coligada_filter,
                            "$skip": skip,
                            "$top": top,
                        },
                    )
                    r.raise_for_status()
                    data = r.json()

                    # OData retorna {value: [...]} ou diretamente lista
                    items = data.get("value") if isinstance(data, dict) else data
                    if not items:
                        break
                    all_items.extend(items)
                    if len(items) < top:
                        break
                    skip += top
        except httpx.HTTPError as exc:
            result.success = False
            result.add_error(f"TOTVS HTTP error: {exc}")
            return result

        for item in all_items:
            try:
                ra = str(self._resolve(item, self.mapping["registration_number"]) or "").strip()
                name = str(self._resolve(item, self.mapping["full_name"]) or "").strip()
                if not ra or not name:
                    continue

                semester_raw = self._resolve(item, self.mapping["semester"])
                semester = int(semester_raw) if semester_raw else None

                # TOTVS usa flags numericas (0=ativo, 1=trancado, 2=formado, ...)
                status_raw = self._resolve(item, self.mapping["enrollment_status"])
                status_map_int = {
                    0: "active",
                    1: "locked",
                    2: "graduated",
                    3: "dropped",
                }
                if isinstance(status_raw, int):
                    enrollment_status = status_map_int.get(status_raw, "active")
                else:
                    enrollment_status = "active"

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

    async def sync_employees(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        endpoint = self.config.get("employees_endpoint")
        if not endpoint:
            result.warnings.append(
                "TOTVS sync_employees: endpoint nao configurado (usar /folha/Funcionario do RM)"
            )
            return result

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                r = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._headers(),
                    params={"$filter": f"CODCOLIGADA eq {self.coligada}"},
                )
                r.raise_for_status()
                data = r.json()
                items = data.get("value") if isinstance(data, dict) else data
        except httpx.HTTPError as exc:
            result.success = False
            result.add_error(f"TOTVS HTTP error (funcionarios): {exc}")
            return result

        for item in items:
            try:
                num = str(item.get("CHAPA") or item.get("MATRICULA") or "").strip()
                name = str(item.get("NOME") or "").strip()
                if not num or not name:
                    continue
                created, _ = await upsert_employee(
                    db,
                    tenant_id,
                    employee_number=num,
                    full_name=name,
                    department=item.get("DEPARTAMENTO"),
                    position=item.get("CARGO"),
                    email=item.get("EMAIL"),
                    phone=item.get("TELEFONE"),
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
        result = SyncResult(success=True)
        result.warnings.append("TOTVS sync_grades nao implementado — recomenda-se busca lazy")
        return result

    async def sync_boletos(self, db, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        result.warnings.append(
            "TOTVS sync_boletos nao implementado — usar endpoint /financeiro/Lancamento"
        )
        return result

    async def sync_all(self, db, tenant_id: uuid.UUID) -> SyncResult:
        start = time.perf_counter()
        s = await self.sync_students(db, tenant_id)
        e = await self.sync_employees(db, tenant_id)
        merged = s.merge(e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "TOTVS sync_all em %dms: tenant=%s registros=%d erros=%d",
            elapsed_ms,
            tenant_id,
            merged.records_synced,
            len(merged.errors),
        )
        return merged
