"""
Fixtures compartilhadas para toda a suite de testes.

- async_db: sessão SQLAlchemy async em memória (SQLite)
- http_client: TestClient do FastAPI
- sample_tenant_id / sample_tenant_id_2: UUIDs fixos para testes de isolamento
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# UUIDs fixos para tornar os testes determinísticos
TENANT_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")
STUDENT_1 = uuid.UUID("cccccccc-0000-0000-0000-000000000001")


@pytest.fixture()
def sample_tenant_id() -> uuid.UUID:
    return TENANT_A


@pytest.fixture()
def sample_tenant_id_2() -> uuid.UUID:
    return TENANT_B


@pytest.fixture()
def sample_student_id() -> uuid.UUID:
    return STUDENT_1


# ── Async DB (SQLite em memória) ──────────────────────────────────────────────

@pytest_asyncio.fixture()
async def async_db():
    """Sessão SQLAlchemy async em SQLite para testes de integração."""
    from app.models.base import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ── Mock DB Session ───────────────────────────────────────────────────────────

@pytest.fixture()
def mock_db() -> AsyncMock:
    """Mock leve de AsyncSession para testes unitários de serviços."""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def http_client():
    """Cliente HTTP assíncrono para testar os endpoints da API."""
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
