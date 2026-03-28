import os

# Set test DATABASE_URL before importing app modules to avoid asyncpg dependency
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import NullPool, StaticPool

# Register SQLite compilation overrides for PostgreSQL-specific types
compiles(JSONB, "sqlite")(lambda element, compiler, **kw: compiler.visit_JSON(element, **kw))


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(element, compiler, **kw):
    return compiler.visit_string(Text(), **kw)


from app.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

_is_sqlite = "sqlite" in TEST_DATABASE_URL
_engine_kwargs: dict = {"echo": False}
if _is_sqlite:
    _engine_kwargs.update(poolclass=StaticPool, connect_args={"check_same_thread": False})
else:
    _engine_kwargs.update(poolclass=NullPool)

test_engine = create_async_engine(TEST_DATABASE_URL, **_engine_kwargs)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(db: AsyncSession) -> Tenant:
    tenant = Tenant(
        name="Faculdade Anchieta Teste",
        slug="anchieta-test",
        plan="basic",
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_admin_user(db: AsyncSession, test_tenant: Tenant) -> User:
    user = User(
        tenant_id=test_tenant.id,
        email="admin@test.com",
        password_hash=hash_password("Test@12345"),
        full_name="Admin Teste",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, test_admin_user: User) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Test@12345"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
