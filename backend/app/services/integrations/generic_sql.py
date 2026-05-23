# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Integrador SQL direto para sistemas academicos legados.

Conecta diretamente ao banco de dados do cliente via SQLAlchemy (sincrono,
executado em thread executor para nao bloquear o event loop).

Suporte:
  - Microsoft SQL Server  (mssql+pymssql)  — TOTVS RM, RM Classis, Microlins
  - MySQL / MariaDB       (mysql+pymysql)  — sistemas menores, open source
  - PostgreSQL            (postgresql+psycopg2) — Moodle, sistemas customizados
  - Oracle                (oracle+oracledb) — sistemas legados de grande porte

Configuracao esperada (campo `config` da AcademicIntegration):
{
  "db_type": "mssql",           # mssql | mysql | postgresql | oracle
  "host": "192.168.1.10",
  "port": 1433,
  "database": "RM",
  "students_query": "SELECT ...",     # ou usar table_mappings abaixo
  "employees_query": "SELECT ...",
  "table_mappings": {
    "students": {
      "table": "SALUNO",
      "registration_number": "CODCOLIGADA",
      "full_name": "NOME",
      "course": "NOMECURSO",
      "semester": "PERIODO",
      "email": "EMAIL",
      "phone": "FONE",
      "status_field": "STATUS",
      "active_value": "A"
    },
    "employees": {
      "table": "PFUNC",
      "employee_number": "CHAPA",
      "full_name": "NOME",
      "department": "SETOR",
      "position": "CARGO",
      "email": "EMAIL",
      "phone": "TELEFONE",
      "status_field": "CODSITUACAO",
      "active_value": "A"
    }
  }
}

Credenciais esperadas:
{
  "username": "sa",
  "password": "senha_secreta"
}
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integrations.base import SyncResult, upsert_employee, upsert_student

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="igs-sql-conn")

DRIVER_MAP = {
    "mssql":      "mssql+pymssql",
    "mysql":      "mysql+pymysql",
    "mariadb":    "mysql+pymysql",
    "postgresql": "postgresql+psycopg2",
    "postgres":   "postgresql+psycopg2",
    "oracle":     "oracle+oracledb",
}


def _build_url(db_type: str, host: str, port: int, database: str, username: str, password: str) -> str:
    driver = DRIVER_MAP.get(db_type.lower())
    if not driver:
        raise ValueError(f"db_type '{db_type}' nao suportado. Use: {', '.join(DRIVER_MAP.keys())}")
    return f"{driver}://{username}:{password}@{host}:{port}/{database}"


def _fetch_rows_sync(conn_url: str, query: str, params: dict | None = None) -> list[dict]:
    """Executa query sincrona e retorna lista de dicts. Roda em thread."""
    from sqlalchemy import create_engine, text

    engine = create_engine(conn_url, pool_pre_ping=True, connect_args={"timeout": 30})
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        engine.dispose()


def _test_connection_sync(conn_url: str) -> tuple[bool, str]:
    """Testa conexao. Roda em thread."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(conn_url, pool_pre_ping=True, connect_args={"timeout": 10})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True, "Conexao estabelecida com sucesso"
    except Exception as exc:
        return False, str(exc)


def _build_students_query(mapping: dict) -> str:
    """Monta SELECT baseado no mapeamento de campos."""
    table = mapping["table"]
    fields = {
        "registration_number": mapping.get("registration_number", "registration_number"),
        "full_name":           mapping.get("full_name", "full_name"),
        "course":              mapping.get("course"),
        "semester":            mapping.get("semester"),
        "email":               mapping.get("email"),
        "phone":               mapping.get("phone"),
        "status_field":        mapping.get("status_field"),
    }
    active_value = mapping.get("active_value", "A")

    select_cols = [
        f"{v} AS {k}"
        for k, v in fields.items()
        if v and k != "status_field"
    ]
    if fields["status_field"]:
        select_cols.append(f"{fields['status_field']} AS _status")

    where = ""
    if fields["status_field"] and active_value:
        where = f" WHERE {fields['status_field']} = '{active_value}'"

    return f"SELECT {', '.join(select_cols)} FROM {table}{where}"


def _build_employees_query(mapping: dict) -> str:
    table = mapping["table"]
    fields = {
        "employee_number": mapping.get("employee_number", "employee_number"),
        "full_name":       mapping.get("full_name", "full_name"),
        "department":      mapping.get("department"),
        "position":        mapping.get("position"),
        "email":           mapping.get("email"),
        "phone":           mapping.get("phone"),
        "status_field":    mapping.get("status_field"),
    }
    active_value = mapping.get("active_value", "A")

    select_cols = [
        f"{v} AS {k}"
        for k, v in fields.items()
        if v and k != "status_field"
    ]
    if fields["status_field"]:
        select_cols.append(f"{fields['status_field']} AS _status")

    where = ""
    if fields["status_field"] and active_value:
        where = f" WHERE {fields['status_field']} = '{active_value}'"

    return f"SELECT {', '.join(select_cols)} FROM {table}{where}"


class GenericSqlIntegrator:
    """Integrador com banco de dados SQL direto."""

    provider_type = "generic_sql"

    def __init__(self, config: dict, credentials: dict) -> None:
        self._config = config
        self._credentials = credentials
        self._conn_url = _build_url(
            db_type=config["db_type"],
            host=config["host"],
            port=int(config.get("port", self._default_port(config["db_type"]))),
            database=config["database"],
            username=credentials["username"],
            password=credentials["password"],
        )

    def _default_port(self, db_type: str) -> int:
        return {"mssql": 1433, "mysql": 3306, "mariadb": 3306, "postgresql": 5432, "postgres": 5432, "oracle": 1521}.get(db_type.lower(), 1433)

    async def test_connection(self) -> tuple[bool, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _test_connection_sync, self._conn_url)

    async def sync_students(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        try:
            query = self._config.get("students_query") or _build_students_query(
                self._config.get("table_mappings", {}).get("students", {})
            )
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(_executor, _fetch_rows_sync, self._conn_url, query)
            for row in rows:
                try:
                    created, _ = await upsert_student(
                        db,
                        tenant_id,
                        registration_number=str(row["registration_number"]),
                        full_name=str(row["full_name"]),
                        course=str(row["course"]) if row.get("course") else None,
                        semester=int(row["semester"]) if row.get("semester") else None,
                        email=str(row["email"]) if row.get("email") else None,
                        phone=str(row["phone"]) if row.get("phone") else None,
                        enrollment_status="active" if row.get("_status", "A") == self._config.get("table_mappings", {}).get("students", {}).get("active_value", "A") else "inactive",
                    )
                    if created:
                        result.students_created += 1
                    else:
                        result.students_updated += 1
                    result.records_synced += 1
                except Exception as exc:
                    result.add_error(f"Aluno {row.get('registration_number', '?')}: {exc}")
        except Exception as exc:
            result.success = False
            result.add_error(f"Falha ao buscar alunos: {exc}")
            logger.exception("Erro sync alunos SQL tenant=%s", tenant_id)
        return result

    async def sync_employees(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        result = SyncResult(success=True)
        try:
            query = self._config.get("employees_query") or _build_employees_query(
                self._config.get("table_mappings", {}).get("employees", {})
            )
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(_executor, _fetch_rows_sync, self._conn_url, query)
            for row in rows:
                try:
                    created, _ = await upsert_employee(
                        db,
                        tenant_id,
                        employee_number=str(row["employee_number"]),
                        full_name=str(row["full_name"]),
                        department=str(row["department"]) if row.get("department") else None,
                        position=str(row["position"]) if row.get("position") else None,
                        email=str(row["email"]) if row.get("email") else None,
                        phone=str(row["phone"]) if row.get("phone") else None,
                    )
                    if created:
                        result.employees_created += 1
                    else:
                        result.employees_updated += 1
                    result.records_synced += 1
                except Exception as exc:
                    result.add_error(f"Func {row.get('employee_number', '?')}: {exc}")
        except Exception as exc:
            result.success = False
            result.add_error(f"Falha ao buscar funcionarios: {exc}")
            logger.exception("Erro sync funcionarios SQL tenant=%s", tenant_id)
        return result

    async def sync_grades(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        # Grades via SQL requer query customizada — usar students_query com grades join
        return SyncResult(success=True, records_synced=0)

    async def sync_boletos(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        return SyncResult(success=True, records_synced=0)

    async def sync_all(self, db: AsyncSession, tenant_id: uuid.UUID) -> SyncResult:
        mappings = self._config.get("table_mappings", {})
        result = SyncResult(success=True)
        if mappings.get("students") or self._config.get("students_query"):
            result = result.merge(await self.sync_students(db, tenant_id))
        if mappings.get("employees") or self._config.get("employees_query"):
            result = result.merge(await self.sync_employees(db, tenant_id))
        return result
