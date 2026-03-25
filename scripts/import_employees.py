"""
Script para importar funcionários via CSV.

Formato do CSV:
employee_number,full_name,department,position,status,email,phone,hire_date

Uso: python scripts/import_employees.py caminho/para/funcionarios.csv [tenant_slug]
"""
import asyncio
import csv
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def import_employees(csv_path: str, tenant_slug: str):
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.config import settings
    from app.models.tenant import Tenant
    from app.models.employee import Employee

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        tenant_result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            print(f"❌ Tenant '{tenant_slug}' não encontrado")
            return

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            created = 0
            skipped = 0

            for row in reader:
                num = row.get("employee_number", "").strip()
                if not num:
                    continue

                existing = await db.execute(
                    select(Employee).where(
                        Employee.tenant_id == tenant.id,
                        Employee.employee_number == num,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                hire_date = None
                if row.get("hire_date"):
                    try:
                        hire_date = date.fromisoformat(row["hire_date"])
                    except ValueError:
                        pass

                employee = Employee(
                    tenant_id=tenant.id,
                    employee_number=num,
                    full_name=row.get("full_name", "").strip(),
                    department=row.get("department", "").strip() or None,
                    position=row.get("position", "").strip() or None,
                    status=row.get("status", "active").strip(),
                    email=row.get("email", "").strip() or None,
                    phone=row.get("phone", "").strip() or None,
                    hire_date=hire_date,
                )
                db.add(employee)
                created += 1

            await db.commit()
            print(f"✅ Importação concluída: {created} criados, {skipped} ignorados")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/import_employees.py <arquivo.csv> <tenant_slug>")
        sys.exit(1)

    asyncio.run(import_employees(sys.argv[1], sys.argv[2]))
