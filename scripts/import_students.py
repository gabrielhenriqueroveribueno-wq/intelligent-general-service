"""
Script para importar alunos via CSV.

Formato do CSV:
registration_number,full_name,course,semester,enrollment_status,email,phone

Uso: python scripts/import_students.py caminho/para/alunos.csv [tenant_slug]
"""
import asyncio
import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def import_students(csv_path: str, tenant_slug: str):
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.config import settings
    from app.models.tenant import Tenant
    from app.models.student import Student

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
                ra = row.get("registration_number", "").strip()
                if not ra:
                    continue

                existing = await db.execute(
                    select(Student).where(
                        Student.tenant_id == tenant.id,
                        Student.registration_number == ra,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                student = Student(
                    tenant_id=tenant.id,
                    registration_number=ra,
                    full_name=row.get("full_name", "").strip(),
                    course=row.get("course", "").strip() or None,
                    semester=int(row["semester"]) if row.get("semester") else None,
                    enrollment_status=row.get("enrollment_status", "active").strip(),
                    email=row.get("email", "").strip() or None,
                    phone=row.get("phone", "").strip() or None,
                )
                db.add(student)
                created += 1

            await db.commit()
            print(f"✅ Importação concluída: {created} criados, {skipped} ignorados (já existiam)")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/import_students.py <arquivo.csv> <tenant_slug>")
        sys.exit(1)

    asyncio.run(import_students(sys.argv[1], sys.argv[2]))
