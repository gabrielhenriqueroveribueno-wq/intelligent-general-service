"""Testes de seguranca do integrador generic_sql.

Cobrem as protecoes contra SQL injection via nomes de identificadores (config do
tenant) e a parametrizacao do valor de filtro (active_value).
"""

import pytest

from app.services.integrations.generic_sql import (
    _build_employees_query,
    _build_students_query,
    _safe_ident,
)


@pytest.mark.unit
def test_safe_ident_accepts_valid_identifiers():
    assert _safe_ident("SALUNO", "table") == "SALUNO"
    assert _safe_ident("dbo.PFUNC", "table") == "dbo.PFUNC"
    assert _safe_ident("COD_COLIGADA$1", "col") == "COD_COLIGADA$1"


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad",
    [
        "SALUNO; DROP TABLE users",
        "NOME OR 1=1",
        "tab'le",
        "col--comment",
        "1abc",
        "",
        "a b",
    ],
)
def test_safe_ident_rejects_injection(bad):
    with pytest.raises(ValueError):
        _safe_ident(bad, "table")


@pytest.mark.unit
def test_build_students_query_parametrizes_active_value():
    mapping = {
        "table": "SALUNO",
        "registration_number": "RA",
        "full_name": "NOME",
        "status_field": "STATUS",
        "active_value": "A",
    }
    sql, params = _build_students_query(mapping)
    # valor de filtro nao deve ser interpolado na string
    assert "'A'" not in sql
    assert ":active_value" in sql
    assert params == {"active_value": "A"}
    assert sql.startswith("SELECT ")
    assert "FROM SALUNO" in sql


@pytest.mark.unit
def test_build_employees_query_rejects_malicious_table():
    mapping = {
        "table": "PFUNC; DELETE FROM students",
        "employee_number": "CHAPA",
        "full_name": "NOME",
    }
    with pytest.raises(ValueError):
        _build_employees_query(mapping)


@pytest.mark.unit
def test_build_students_query_without_status_has_no_where():
    sql, params = _build_students_query(
        {"table": "SALUNO", "registration_number": "RA", "full_name": "NOME"}
    )
    assert "WHERE" not in sql
    assert params == {}
