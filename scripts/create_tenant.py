"""
Script para criar um novo tenant (instituição) no sistema.

Uso: python scripts/create_tenant.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def create_tenant():
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.config import settings
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.utils.security import hash_password

    print("=== Criar Novo Tenant ===\n")
    name = input("Nome da instituição: ").strip()
    slug = input("Slug (ex: anchieta): ").strip().lower()
    plan = input("Plano [basic/pro/enterprise] (default: basic): ").strip() or "basic"
    admin_email = input("Email do admin: ").strip()
    admin_password = input("Senha do admin: ").strip()
    admin_name = input("Nome completo do admin: ").strip()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        from sqlalchemy import select

        existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
        if existing.scalar_one_or_none():
            print(f"\n❌ Erro: Slug '{slug}' já existe.")
            return

        tenant = Tenant(name=name, slug=slug, plan=plan)
        db.add(tenant)
        await db.flush()

        admin = User(
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=admin_name,
            role="admin",
        )
        db.add(admin)
        await db.commit()

        print(f"\n✅ Tenant criado com sucesso!")
        print(f"   ID: {tenant.id}")
        print(f"   Nome: {name}")
        print(f"   Slug: {slug}")
        print(f"   Admin: {admin_email}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tenant())
