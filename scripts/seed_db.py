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
from app.models.employee import Employee, Payslip, VacationBalance, TimeRecord
from app.models.knowledge_base import KBCategory, KBArticle
from app.models.billing import Boleto
from app.models.schedule import ClassSchedule
from app.models.audit import SLAConfig
from app.utils.security import hash_password
from datetime import date, time, datetime, timezone
from decimal import Decimal


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

            # Buscar alunos e funcionários recém-criados para associar dados
            result_students = await db.execute(
                select(Student).where(Student.tenant_id == tenant.id)
            )
            all_students = result_students.scalars().all()

            result_employees = await db.execute(
                select(Employee).where(Employee.tenant_id == tenant.id)
            )
            all_employees = result_employees.scalars().all()

            # ── Notas (Grades) ────────────────────────────────────────────
            subjects_by_course = {
                "Administração": [
                    ("ADM101", "Introdução à Administração"),
                    ("ADM102", "Contabilidade Básica"),
                    ("ADM103", "Matemática Financeira"),
                ],
                "Engenharia de Software": [
                    ("ENG201", "Algoritmos e Estrutura de Dados"),
                    ("ENG202", "Banco de Dados"),
                    ("ENG203", "Engenharia de Requisitos"),
                    ("ENG204", "Programação Web"),
                ],
                "Pedagogia": [
                    ("PED101", "Fundamentos da Educação"),
                    ("PED102", "Psicologia do Desenvolvimento"),
                    ("PED103", "Didática Geral"),
                ],
                "Direito": [
                    ("DIR301", "Direito Constitucional"),
                    ("DIR302", "Direito Civil I"),
                    ("DIR303", "Direito Penal I"),
                    ("DIR304", "Teoria Geral do Processo"),
                ],
            }
            grade_values = [
                (Decimal("8.50"), "P1"), (Decimal("7.00"), "P2"),
                (Decimal("9.00"), "P1"), (Decimal("6.50"), "P2"),
                (Decimal("7.50"), "P1"), (Decimal("8.00"), "P2"),
                (Decimal("5.50"), "P1"), (Decimal("9.50"), "P2"),
            ]
            gv_idx = 0
            for student in all_students:
                course_subjects = subjects_by_course.get(student.course, [])
                for code, name in course_subjects:
                    for gv, gt in [grade_values[gv_idx % len(grade_values)],
                                   grade_values[(gv_idx + 1) % len(grade_values)]]:
                        grade = Grade(
                            tenant_id=tenant.id,
                            student_id=student.id,
                            subject_name=name,
                            subject_code=code,
                            academic_period="2026.1",
                            grade_value=gv,
                            grade_type=gt,
                            status="approved" if gv >= Decimal("6.0") else "failed",
                        )
                        db.add(grade)
                    gv_idx += 1

            # ── Frequência (Attendance) ───────────────────────────────────
            for student in all_students:
                course_subjects = subjects_by_course.get(student.course, [])
                for code, name in course_subjects:
                    total = 40
                    attended = total - (hash(student.full_name + code) % 8)
                    absence = round(Decimal(str((total - attended) / total * 100)), 2)
                    att = AttendanceRecord(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        subject_code=code,
                        subject_name=name,
                        academic_period="2026.1",
                        total_classes=total,
                        attended=attended,
                        absence_pct=absence,
                    )
                    db.add(att)

            # ── Boletos ───────────────────────────────────────────────────
            for student in all_students:
                for month_num in range(1, 4):  # Jan, Fev, Mar 2026
                    ref = f"2026-{month_num:02d}"
                    is_paid = month_num <= 2  # Jan e Fev pagos, Mar pendente
                    boleto = Boleto(
                        tenant_id=tenant.id,
                        student_id=student.id,
                        reference_month=ref,
                        amount=Decimal("1250.00"),
                        due_date=date(2026, month_num, 10),
                        status="paid" if is_paid else "pending",
                        barcode=f"23793.38128 60000.00000{student.registration_number} {month_num:02d}000.000000 1 {90 + month_num}260000125000",
                    )
                    db.add(boleto)

            # ── Grade Horária (Class Schedules) ───────────────────────────
            schedule_data = [
                ("Administração", 2, "ADM101", "Introdução à Administração", 0, "08:00", "09:40", "Sala 201", "Prof. Ricardo Almeida"),
                ("Administração", 2, "ADM102", "Contabilidade Básica", 1, "08:00", "09:40", "Sala 202", "Profa. Sandra Lima"),
                ("Administração", 2, "ADM103", "Matemática Financeira", 2, "10:00", "11:40", "Sala 201", "Prof. Marcos Pereira"),
                ("Engenharia de Software", 4, "ENG201", "Algoritmos e Estrutura de Dados", 0, "19:00", "20:40", "Lab 01", "Prof. André Silva"),
                ("Engenharia de Software", 4, "ENG202", "Banco de Dados", 1, "19:00", "20:40", "Lab 02", "Profa. Julia Santos"),
                ("Engenharia de Software", 4, "ENG203", "Engenharia de Requisitos", 2, "21:00", "22:40", "Sala 301", "Prof. Felipe Costa"),
                ("Engenharia de Software", 4, "ENG204", "Programação Web", 3, "19:00", "20:40", "Lab 01", "Prof. André Silva"),
                ("Pedagogia", 1, "PED101", "Fundamentos da Educação", 0, "14:00", "15:40", "Sala 101", "Profa. Ana Beatriz"),
                ("Pedagogia", 1, "PED102", "Psicologia do Desenvolvimento", 2, "14:00", "15:40", "Sala 102", "Prof. Henrique Nunes"),
                ("Pedagogia", 1, "PED103", "Didática Geral", 4, "14:00", "15:40", "Sala 101", "Profa. Cláudia Rocha"),
                ("Direito", 6, "DIR301", "Direito Constitucional", 0, "08:00", "09:40", "Sala 401", "Prof. Eduardo Bastos"),
                ("Direito", 6, "DIR302", "Direito Civil I", 1, "10:00", "11:40", "Sala 402", "Profa. Luciana Torres"),
                ("Direito", 6, "DIR303", "Direito Penal I", 3, "08:00", "09:40", "Sala 401", "Prof. Roberto Campos"),
                ("Direito", 6, "DIR304", "Teoria Geral do Processo", 4, "10:00", "11:40", "Sala 403", "Prof. Thiago Moreira"),
            ]
            for course, sem, code, name, dow, start, end, room, prof in schedule_data:
                h_start, m_start = map(int, start.split(":"))
                h_end, m_end = map(int, end.split(":"))
                cs = ClassSchedule(
                    tenant_id=tenant.id,
                    course=course,
                    semester=sem,
                    subject_name=name,
                    subject_code=code,
                    day_of_week=dow,
                    start_time=time(h_start, m_start),
                    end_time=time(h_end, m_end),
                    room=room,
                    professor=prof,
                    academic_period="2026.1",
                )
                db.add(cs)

            # ── Holerites (Payslips) ──────────────────────────────────────
            salary_data = {
                "FUNC001": (Decimal("3500.00"), "Secretária"),
                "FUNC002": (Decimal("5200.00"), "Analista de RH"),
                "FUNC003": (Decimal("6800.00"), "Analista de TI"),
            }
            for emp in all_employees:
                gross, _ = salary_data.get(emp.employee_number, (Decimal("3000.00"), ""))
                for month_num in range(1, 4):
                    inss = round(gross * Decimal("0.11"), 2)
                    irrf = round(gross * Decimal("0.075"), 2) if gross > Decimal("3000") else Decimal("0.00")
                    vt = Decimal("220.00")
                    net = gross - inss - irrf - vt
                    payslip = Payslip(
                        tenant_id=tenant.id,
                        employee_id=emp.id,
                        reference_month=f"2026-{month_num:02d}",
                        gross_salary=gross,
                        net_salary=net,
                        deductions={"INSS": str(inss), "IRRF": str(irrf), "Vale Transporte": str(vt)},
                    )
                    db.add(payslip)

            # ── Saldo de Férias (Vacation Balances) ───────────────────────
            for emp in all_employees:
                vb = VacationBalance(
                    tenant_id=tenant.id,
                    employee_id=emp.id,
                    accrual_period_start=date(2025, 3, 1),
                    accrual_period_end=date(2026, 2, 28),
                    total_days=30,
                    used_days=0 if emp.employee_number != "FUNC001" else 10,
                    deadline_date=date(2027, 2, 28),
                )
                db.add(vb)

            # ── Registros de Ponto (Time Records) - última semana ─────────
            for emp in all_employees:
                for day_offset in range(5):  # Seg a Sex da semana atual
                    rec_date = date(2026, 3, 23 + day_offset)
                    tr = TimeRecord(
                        tenant_id=tenant.id,
                        employee_id=emp.id,
                        record_date=rec_date,
                        clock_in=datetime(2026, 3, 23 + day_offset, 8, 0, tzinfo=timezone.utc),
                        clock_out=datetime(2026, 3, 23 + day_offset, 17, 0, tzinfo=timezone.utc),
                        break_start=datetime(2026, 3, 23 + day_offset, 12, 0, tzinfo=timezone.utc),
                        break_end=datetime(2026, 3, 23 + day_offset, 13, 0, tzinfo=timezone.utc),
                        total_hours=Decimal("8.00"),
                        status="regular",
                    )
                    db.add(tr)

            print("✓ Dados de exemplo criados (KB, alunos, funcionários, SLA, notas, frequência, boletos, horários, holerites, férias, ponto)")
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
