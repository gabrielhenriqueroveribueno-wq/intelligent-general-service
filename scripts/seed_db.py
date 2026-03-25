"""
Script de seed inicial do banco de dados.
Cria o super admin e um tenant de exemplo com dados de teste.

Uso: python scripts/seed_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.models.base import Base
from app.models.tenant import Tenant, TenantSettings
from app.models.user import User
from app.models.student import Student, Grade, AttendanceRecord
from app.models.employee import Employee, Payslip, VacationBalance
from app.models.knowledge_base import KBCategory, KBArticle
from app.models.audit import SLAConfig
from app.utils.security import hash_password


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tabelas criadas/verificadas")

    async with async_session() as db:
        # ── Super Admin ────────────────────────────────────────────────────
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == settings.SUPER_ADMIN_EMAIL))
        if not existing.scalar_one_or_none():
            super_admin = User(
                email=settings.SUPER_ADMIN_EMAIL,
                password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
                full_name=settings.SUPER_ADMIN_NAME,
                role="super_admin",
                tenant_id=None,
            )
            db.add(super_admin)
            print(f"✓ Super admin criado: {settings.SUPER_ADMIN_EMAIL}")
        else:
            print(f"→ Super admin já existe: {settings.SUPER_ADMIN_EMAIL}")

        # ── Tenant de Exemplo ──────────────────────────────────────────────
        existing_t = await db.execute(select(Tenant).where(Tenant.slug == "anchieta"))
        tenant = existing_t.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                name="Faculdade Anchieta",
                slug="anchieta",
                plan="pro",
                whatsapp_phone="+5511999999999",
                settings={"bot_name": "Assistente Anchieta"},
            )
            db.add(tenant)
            await db.flush()
            print(f"✓ Tenant criado: Faculdade Anchieta (slug=anchieta)")

            # Admin do tenant
            admin = User(
                tenant_id=tenant.id,
                email="gestor@anchieta.edu.br",
                password_hash=hash_password("Gestor@2026"),
                full_name="Gestor Anchieta",
                role="admin",
            )
            db.add(admin)

            # Configurações do tenant
            ts = TenantSettings(
                tenant_id=tenant.id,
                bot_name="Assistente Anchieta",
                welcome_message="Olá! Bem-vindo à Faculdade Anchieta. Como posso ajudar?",
                business_hours_start="08:00",
                business_hours_end="22:00",
                business_days="1,2,3,4,5,6",
            )
            db.add(ts)

            # SLA configs
            for priority, response_min, resolution_min in [
                ("low", 120, 1440),
                ("medium", 60, 480),
                ("high", 30, 240),
                ("critical", 15, 60),
            ]:
                sla = SLAConfig(
                    tenant_id=tenant.id,
                    priority=priority,
                    response_time_minutes=response_min,
                    resolution_time_minutes=resolution_min,
                )
                db.add(sla)

            # KB Categories
            cat_aluno = KBCategory(tenant_id=tenant.id, name="Alunos", sort_order=1)
            cat_rh = KBCategory(tenant_id=tenant.id, name="RH / Funcionários", sort_order=2)
            cat_geral = KBCategory(tenant_id=tenant.id, name="Geral", sort_order=3)
            db.add_all([cat_aluno, cat_rh, cat_geral])
            await db.flush()

            # KB Articles
            articles = [
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_aluno.id,
                    title="Como consultar minhas notas?",
                    content="Para consultar suas notas, envie 'minhas notas' ou 'notas de [disciplina]'. O sistema irá exibir suas notas do período atual.",
                    applies_to="student",
                    keywords=["notas", "grades", "avaliação", "prova"],
                ),
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_aluno.id,
                    title="Como obter 2ª via de boleto?",
                    content="Para obter a 2ª via do seu boleto, envie '2ª via boleto' ou 'boleto'. O sistema irá exibir seus boletos em aberto com o código de barras.",
                    applies_to="student",
                    keywords=["boleto", "pagamento", "mensalidade", "2a via"],
                ),
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_aluno.id,
                    title="Como verificar minha frequência?",
                    content="Para verificar sua frequência, envie 'minha frequência' ou 'faltas'. O sistema mostrará o percentual de presença por disciplina.",
                    applies_to="student",
                    keywords=["frequência", "faltas", "presença", "falta"],
                ),
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_rh.id,
                    title="Como consultar meu holerite?",
                    content="Para consultar seu holerite, envie 'holerite' ou 'contracheque'. O sistema mostrará seu holerite do mês atual e dos meses anteriores.",
                    applies_to="employee",
                    keywords=["holerite", "salário", "contracheque", "pagamento"],
                ),
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_rh.id,
                    title="Como verificar saldo de férias?",
                    content="Para verificar seu saldo de férias, envie 'férias' ou 'saldo férias'. O sistema mostrará seus dias disponíveis e o prazo para tirar férias.",
                    applies_to="employee",
                    keywords=["férias", "descanso", "saldo", "dias"],
                ),
                KBArticle(
                    tenant_id=tenant.id,
                    category_id=cat_geral.id,
                    title="Horários de funcionamento",
                    content="A Faculdade Anchieta funciona de segunda a sábado, das 7h às 23h. A secretaria atende de segunda a sexta, das 8h às 18h, e aos sábados das 8h às 12h.",
                    applies_to="all",
                    keywords=["horário", "funcionamento", "atendimento", "secretaria"],
                ),
            ]
            db.add_all(articles)

            # Alunos de exemplo
            students_data = [
                ("12345", "Ana Paula Souza", "Administração", 2),
                ("12346", "Bruno Ferreira", "Engenharia de Software", 4),
                ("12347", "Carla Mendes", "Pedagogia", 1),
                ("12348", "Diego Santos", "Direito", 6),
            ]
            for ra, name, course, semester in students_data:
                student = Student(
                    tenant_id=tenant.id,
                    registration_number=ra,
                    full_name=name,
                    course=course,
                    semester=semester,
                    enrollment_status="active",
                    email=f"{ra}@aluno.anchieta.edu.br",
                )
                db.add(student)

            await db.flush()

            # Funcionários de exemplo
            employees_data = [
                ("FUNC001", "Maria Rodrigues", "Secretaria", "Secretária"),
                ("FUNC002", "Carlos Oliveira", "RH", "Analista de RH"),
                ("FUNC003", "Fernanda Costa", "TI", "Analista de TI"),
            ]
            for num, name, dept, pos in employees_data:
                employee = Employee(
                    tenant_id=tenant.id,
                    employee_number=num,
                    full_name=name,
                    department=dept,
                    position=pos,
                    status="active",
                    email=f"{num.lower()}@anchieta.edu.br",
                )
                db.add(employee)

            print("✓ Dados de exemplo criados (KB, alunos, funcionários, SLA)")
        else:
            print(f"→ Tenant já existe: Faculdade Anchieta")

        await db.commit()
        print("\n✅ Seed concluído com sucesso!")
        print(f"\n📋 Credenciais:")
        print(f"   Super Admin: {settings.SUPER_ADMIN_EMAIL} / {settings.SUPER_ADMIN_PASSWORD}")
        print(f"   Admin Tenant: gestor@anchieta.edu.br / Gestor@2026")
        print(f"\n🚀 API disponível em: http://localhost:8000/docs")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
