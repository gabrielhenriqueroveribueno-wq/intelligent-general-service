"""
Script de seed para DEMO / Pitch Deck.

Cria dados fictícios completos para demonstração:
- Super admin + tenant Anchieta
- Admin, agentes, professores
- Alunos com notas, frequência, boletos, horários
- Funcionários com holerites, férias, ponto, solicitações RH
- Contatos WhatsApp vinculados
- Conversas com mensagens realistas
- Tickets com diferentes status e SLA
- Templates de slides + apresentações geradas
- Knowledge Base completa
- Templates de mensagem
- Pesquisas de satisfação
- Métricas de resposta

Uso: python scripts/seed_demo.py
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base
from app.models.billing import Boleto
from app.models.conversation import Contact, Conversation, Message
from app.models.employee import Employee, HRRequest, Payslip, TimeRecord, VacationBalance
from app.models.knowledge_base import KBArticle, KBCategory
from app.models.metrics import ResponseTimeMetric
from app.models.notification import MessageTemplate, ScheduledNotification
from app.models.satisfaction import SatisfactionSurvey
from app.models.schedule import ClassSchedule
from app.models.audit import AuditLog, SLAConfig
from app.models.slide import SlideGenerationLog, SlidePresentation, SlideTemplate
from app.models.student import AttendanceRecord, Grade, Student
from app.models.tenant import Tenant, TenantSettings
from app.models.ticket import Ticket, TicketComment
from app.models.ticket_learning import TicketResolution
from app.models.user import User
from app.utils.security import hash_password

NOW = datetime.now(timezone.utc)


async def seed_demo():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tabelas criadas/verificadas")

    async with async_session() as db:
        # ══════════════════════════════════════════════════════════════════
        # 1. SUPER ADMIN
        # ══════════════════════════════════════════════════════════════════
        existing = await db.execute(
            select(User).where(User.email == settings.SUPER_ADMIN_EMAIL)
        )
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
            print(f"→ Super admin já existe")

        # ══════════════════════════════════════════════════════════════════
        # 2. TENANT
        # ══════════════════════════════════════════════════════════════════
        existing_t = await db.execute(select(Tenant).where(Tenant.slug == "anchieta"))
        tenant = existing_t.scalar_one_or_none()

        if tenant:
            print("→ Tenant Anchieta já existe, pulando seed de demo.")
            print("   Para recriar, delete o tenant e rode novamente.")
            await db.commit()
            await engine.dispose()
            return

        tenant = Tenant(
            name="Faculdade Anchieta",
            slug="anchieta",
            plan="pro",
            whatsapp_phone="+5511999999999",
            settings={"bot_name": "Assistente Anchieta"},
        )
        db.add(tenant)
        await db.flush()
        tenant_id = tenant.id
        print(f"✓ Tenant criado: Faculdade Anchieta")

        # ══════════════════════════════════════════════════════════════════
        # 3. USERS (Admin, Agentes, Professores)
        # ══════════════════════════════════════════════════════════════════
        admin = User(
            tenant_id=tenant_id,
            email="gestor@anchieta.edu.br",
            password_hash=hash_password("Gestor@2026"),
            full_name="Gestor Anchieta",
            role="admin",
        )
        db.add(admin)

        agent1 = User(
            tenant_id=tenant_id,
            email="suporte1@anchieta.edu.br",
            password_hash=hash_password("Suporte@2026"),
            full_name="Camila Dias - Suporte",
            role="agent",
        )
        agent2 = User(
            tenant_id=tenant_id,
            email="suporte2@anchieta.edu.br",
            password_hash=hash_password("Suporte@2026"),
            full_name="Rafael Moreira - Suporte",
            role="agent",
        )
        db.add_all([agent1, agent2])

        teacher1 = User(
            tenant_id=tenant_id,
            email="prof.andre@anchieta.edu.br",
            password_hash=hash_password("Prof@2026"),
            full_name="Prof. André Silva",
            role="teacher",
        )
        teacher2 = User(
            tenant_id=tenant_id,
            email="prof.julia@anchieta.edu.br",
            password_hash=hash_password("Prof@2026"),
            full_name="Profa. Julia Santos",
            role="teacher",
        )
        teacher3 = User(
            tenant_id=tenant_id,
            email="prof.ana@anchieta.edu.br",
            password_hash=hash_password("Prof@2026"),
            full_name="Profa. Ana Beatriz",
            role="teacher",
        )
        db.add_all([teacher1, teacher2, teacher3])
        await db.flush()
        print("✓ Usuários criados: admin, 2 agentes, 3 professores")

        # ══════════════════════════════════════════════════════════════════
        # 4. TENANT SETTINGS + SLA
        # ══════════════════════════════════════════════════════════════════
        ts = TenantSettings(
            tenant_id=tenant_id,
            bot_name="Assistente Anchieta",
            welcome_message="Olá! 👋 Bem-vindo à Faculdade Anchieta. Como posso ajudar?",
            business_hours_start="08:00",
            business_hours_end="22:00",
            business_days="1,2,3,4,5,6",
        )
        db.add(ts)

        for priority, response_min, resolution_min in [
            ("low", 120, 1440),
            ("medium", 60, 480),
            ("high", 30, 240),
            ("critical", 15, 60),
        ]:
            db.add(SLAConfig(
                tenant_id=tenant_id,
                priority=priority,
                response_time_minutes=response_min,
                resolution_time_minutes=resolution_min,
            ))
        print("✓ Configurações e SLA criados")

        # ══════════════════════════════════════════════════════════════════
        # 5. KNOWLEDGE BASE
        # ══════════════════════════════════════════════════════════════════
        cat_aluno = KBCategory(tenant_id=tenant_id, name="Alunos", sort_order=1)
        cat_rh = KBCategory(tenant_id=tenant_id, name="RH / Funcionários", sort_order=2)
        cat_geral = KBCategory(tenant_id=tenant_id, name="Geral", sort_order=3)
        cat_financeiro = KBCategory(tenant_id=tenant_id, name="Financeiro", sort_order=4)
        cat_academico = KBCategory(tenant_id=tenant_id, name="Acadêmico", sort_order=5)
        db.add_all([cat_aluno, cat_rh, cat_geral, cat_financeiro, cat_academico])
        await db.flush()

        articles = [
            KBArticle(tenant_id=tenant_id, category_id=cat_aluno.id,
                      title="Como consultar minhas notas?",
                      content="Para consultar suas notas, envie 'minhas notas' ou 'notas de [disciplina]'. O sistema irá exibir suas notas do período atual.",
                      applies_to="student", keywords=["notas", "grades", "avaliação", "prova"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_aluno.id,
                      title="Como obter 2ª via de boleto?",
                      content="Para obter a 2ª via do seu boleto, envie '2ª via boleto' ou 'boleto'. O sistema irá exibir seus boletos em aberto com o código de barras.",
                      applies_to="student", keywords=["boleto", "pagamento", "mensalidade", "2a via"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_aluno.id,
                      title="Como verificar minha frequência?",
                      content="Para verificar sua frequência, envie 'minha frequência' ou 'faltas'. O sistema mostrará o percentual de presença por disciplina.",
                      applies_to="student", keywords=["frequência", "faltas", "presença"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_aluno.id,
                      title="Como ver meus horários de aula?",
                      content="Envie 'meus horários' ou 'grade horária'. O sistema mostrará suas aulas da semana com sala e professor.",
                      applies_to="student", keywords=["horário", "grade", "aula", "sala"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_rh.id,
                      title="Como consultar meu holerite?",
                      content="Para consultar seu holerite, envie 'holerite' ou 'contracheque'. O sistema mostrará seu holerite do mês atual e anteriores.",
                      applies_to="employee", keywords=["holerite", "salário", "contracheque"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_rh.id,
                      title="Como verificar saldo de férias?",
                      content="Envie 'férias' ou 'saldo férias'. O sistema mostrará seus dias disponíveis e prazo.",
                      applies_to="employee", keywords=["férias", "descanso", "saldo"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_rh.id,
                      title="Como consultar meu ponto?",
                      content="Envie 'meu ponto' ou 'registro de ponto'. O sistema mostrará seus registros de entrada/saída da semana.",
                      applies_to="employee", keywords=["ponto", "registro", "entrada", "saída"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_rh.id,
                      title="Como enviar atestado médico?",
                      content="Envie 'atestado' ou 'solicitar atestado' para registrar um atestado médico. Você será orientado a enviar a foto do documento.",
                      applies_to="employee", keywords=["atestado", "médico", "afastamento"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_financeiro.id,
                      title="Negociação de débitos",
                      content="Para negociar débitos ou parcelar mensalidades em atraso, envie 'negociar débito'. A secretaria financeira entrará em contato em até 48h.",
                      applies_to="student", keywords=["negociação", "débito", "parcelar", "atraso"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_financeiro.id,
                      title="Bolsas e descontos",
                      content="Para informações sobre bolsas de estudo e programas de desconto, envie 'bolsa' ou 'desconto'. Consulte os programas disponíveis: PROUNI, FIES, Bolsa Mérito e convênios empresariais.",
                      applies_to="student", keywords=["bolsa", "desconto", "PROUNI", "FIES"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_academico.id,
                      title="Calendário acadêmico",
                      content="O semestre 2026.1 vai de 03/02 a 30/06. Período de provas P1: 31/03 a 11/04. Provas P2: 09/06 a 20/06. Recesso: 01/07 a 31/07.",
                      applies_to="all", keywords=["calendário", "semestre", "provas", "recesso"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_academico.id,
                      title="Trancamento de matrícula",
                      content="O trancamento pode ser solicitado até 30 dias antes do fim do semestre. Envie 'trancamento' para iniciar o processo.",
                      applies_to="student", keywords=["trancamento", "trancar", "suspender"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_geral.id,
                      title="Horários de funcionamento",
                      content="A Faculdade Anchieta funciona de segunda a sábado, das 7h às 23h. Secretaria: seg-sex 8h-18h, sáb 8h-12h.",
                      applies_to="all", keywords=["horário", "funcionamento", "secretaria"]),
            KBArticle(tenant_id=tenant_id, category_id=cat_geral.id,
                      title="Contatos da instituição",
                      content="Secretaria: (11) 3333-4444 | Financeiro: (11) 3333-4445 | Coordenação: (11) 3333-4446 | Email: contato@anchieta.edu.br",
                      applies_to="all", keywords=["contato", "telefone", "email"]),
        ]
        db.add_all(articles)
        print("✓ Knowledge Base: 5 categorias, 14 artigos")

        # ══════════════════════════════════════════════════════════════════
        # 6. ALUNOS
        # ══════════════════════════════════════════════════════════════════
        students_data = [
            ("12345", "Ana Paula Souza", "Administração", 2, "+5511988881111", "ana.souza@email.com"),
            ("12346", "Bruno Ferreira", "Engenharia de Software", 4, "+5511988882222", "bruno.f@email.com"),
            ("12347", "Carla Mendes", "Pedagogia", 1, "+5511988883333", "carla.m@email.com"),
            ("12348", "Diego Santos", "Direito", 6, "+5511988884444", "diego.s@email.com"),
            ("12349", "Elena Rodrigues", "Administração", 4, "+5511988885555", "elena.r@email.com"),
            ("12350", "Felipe Almeida", "Engenharia de Software", 2, "+5511988886666", "felipe.a@email.com"),
            ("12351", "Giovana Costa", "Pedagogia", 3, "+5511988887777", "giovana.c@email.com"),
            ("12352", "Henrique Lima", "Direito", 2, "+5511988888888", "henrique.l@email.com"),
        ]
        all_students = []
        for ra, name, course, semester, phone, email in students_data:
            student = Student(
                tenant_id=tenant_id,
                registration_number=ra,
                full_name=name,
                course=course,
                semester=semester,
                enrollment_status="active",
                email=email,
                phone=phone,
            )
            db.add(student)
            all_students.append(student)
        await db.flush()
        print(f"✓ {len(all_students)} alunos criados")

        # ══════════════════════════════════════════════════════════════════
        # 7. FUNCIONÁRIOS
        # ══════════════════════════════════════════════════════════════════
        employees_data = [
            ("FUNC001", "Maria Rodrigues", "Secretaria", "Secretária", "+5511977771111", date(2020, 3, 15)),
            ("FUNC002", "Carlos Oliveira", "RH", "Analista de RH", "+5511977772222", date(2019, 7, 1)),
            ("FUNC003", "Fernanda Costa", "TI", "Analista de TI", "+5511977773333", date(2021, 1, 10)),
            ("FUNC004", "Roberto Nascimento", "Financeiro", "Auxiliar Financeiro", "+5511977774444", date(2022, 5, 20)),
            ("FUNC005", "Patrícia Alves", "Coordenação", "Coordenadora Pedagógica", "+5511977775555", date(2018, 2, 1)),
        ]
        all_employees = []
        for num, name, dept, pos, phone, hire in employees_data:
            emp = Employee(
                tenant_id=tenant_id,
                employee_number=num,
                full_name=name,
                department=dept,
                position=pos,
                status="active",
                email=f"{num.lower()}@anchieta.edu.br",
                phone=phone,
                hire_date=hire,
            )
            db.add(emp)
            all_employees.append(emp)
        await db.flush()
        print(f"✓ {len(all_employees)} funcionários criados")

        # ══════════════════════════════════════════════════════════════════
        # 8. NOTAS (Grades)
        # ══════════════════════════════════════════════════════════════════
        subjects_by_course = {
            "Administração": [
                ("ADM101", "Introdução à Administração"),
                ("ADM102", "Contabilidade Básica"),
                ("ADM103", "Matemática Financeira"),
                ("ADM201", "Marketing I"),
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
                ("PED104", "Sociologia da Educação"),
            ],
            "Direito": [
                ("DIR301", "Direito Constitucional"),
                ("DIR302", "Direito Civil I"),
                ("DIR303", "Direito Penal I"),
                ("DIR304", "Teoria Geral do Processo"),
            ],
        }
        grade_values = [
            Decimal("8.50"), Decimal("7.00"), Decimal("9.00"), Decimal("6.50"),
            Decimal("7.50"), Decimal("8.00"), Decimal("5.50"), Decimal("9.50"),
            Decimal("4.00"), Decimal("10.00"), Decimal("6.00"), Decimal("8.75"),
        ]
        gv_idx = 0
        for student in all_students:
            course_subjects = subjects_by_course.get(student.course, [])
            for code, name in course_subjects:
                for grade_type in ["P1", "P2"]:
                    gv = grade_values[gv_idx % len(grade_values)]
                    db.add(Grade(
                        tenant_id=tenant_id,
                        student_id=student.id,
                        subject_name=name,
                        subject_code=code,
                        academic_period="2026.1",
                        grade_value=gv,
                        grade_type=grade_type,
                        status="approved" if gv >= Decimal("6.0") else "failed",
                    ))
                    gv_idx += 1
        print("✓ Notas criadas para todos os alunos")

        # ══════════════════════════════════════════════════════════════════
        # 9. FREQUÊNCIA
        # ══════════════════════════════════════════════════════════════════
        for student in all_students:
            course_subjects = subjects_by_course.get(student.course, [])
            for code, name in course_subjects:
                total = 40
                attended = total - (hash(student.full_name + code) % 8)
                absence = round(Decimal(str((total - attended) / total * 100)), 2)
                db.add(AttendanceRecord(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    subject_code=code,
                    subject_name=name,
                    academic_period="2026.1",
                    total_classes=total,
                    attended=attended,
                    absence_pct=absence,
                ))
        print("✓ Frequência criada para todos os alunos")

        # ══════════════════════════════════════════════════════════════════
        # 10. BOLETOS
        # ══════════════════════════════════════════════════════════════════
        for student in all_students:
            for month_num in range(1, 5):  # Jan-Abr 2026
                is_paid = month_num <= 2
                db.add(Boleto(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    reference_month=f"2026-{month_num:02d}",
                    amount=Decimal("1250.00"),
                    due_date=date(2026, month_num, 10),
                    status="paid" if is_paid else ("pending" if month_num == 3 else "overdue"),
                    barcode=f"23793.38128 60000.00000{student.registration_number} {month_num:02d}000.000000 1 {90 + month_num}260000125000",
                ))
        print("✓ Boletos criados (jan-abr, 2 pagos, 1 pendente, 1 vencido)")

        # ══════════════════════════════════════════════════════════════════
        # 11. GRADE HORÁRIA
        # ══════════════════════════════════════════════════════════════════
        schedule_data = [
            ("Administração", 2, "ADM101", "Introdução à Administração", 0, "08:00", "09:40", "Sala 201", "Prof. Ricardo Almeida"),
            ("Administração", 2, "ADM102", "Contabilidade Básica", 1, "08:00", "09:40", "Sala 202", "Profa. Sandra Lima"),
            ("Administração", 2, "ADM103", "Matemática Financeira", 2, "10:00", "11:40", "Sala 201", "Prof. Marcos Pereira"),
            ("Administração", 4, "ADM201", "Marketing I", 3, "08:00", "09:40", "Sala 203", "Prof. Lucas Barros"),
            ("Engenharia de Software", 4, "ENG201", "Algoritmos e Estrutura de Dados", 0, "19:00", "20:40", "Lab 01", "Prof. André Silva"),
            ("Engenharia de Software", 4, "ENG202", "Banco de Dados", 1, "19:00", "20:40", "Lab 02", "Profa. Julia Santos"),
            ("Engenharia de Software", 4, "ENG203", "Engenharia de Requisitos", 2, "21:00", "22:40", "Sala 301", "Prof. Felipe Costa"),
            ("Engenharia de Software", 4, "ENG204", "Programação Web", 3, "19:00", "20:40", "Lab 01", "Prof. André Silva"),
            ("Engenharia de Software", 2, "ENG201", "Algoritmos e Estrutura de Dados", 0, "19:00", "20:40", "Lab 01", "Prof. André Silva"),
            ("Engenharia de Software", 2, "ENG202", "Banco de Dados", 2, "19:00", "20:40", "Lab 02", "Profa. Julia Santos"),
            ("Pedagogia", 1, "PED101", "Fundamentos da Educação", 0, "14:00", "15:40", "Sala 101", "Profa. Ana Beatriz"),
            ("Pedagogia", 1, "PED102", "Psicologia do Desenvolvimento", 2, "14:00", "15:40", "Sala 102", "Prof. Henrique Nunes"),
            ("Pedagogia", 1, "PED103", "Didática Geral", 4, "14:00", "15:40", "Sala 101", "Profa. Cláudia Rocha"),
            ("Pedagogia", 3, "PED104", "Sociologia da Educação", 1, "14:00", "15:40", "Sala 103", "Profa. Ana Beatriz"),
            ("Direito", 6, "DIR301", "Direito Constitucional", 0, "08:00", "09:40", "Sala 401", "Prof. Eduardo Bastos"),
            ("Direito", 6, "DIR302", "Direito Civil I", 1, "10:00", "11:40", "Sala 402", "Profa. Luciana Torres"),
            ("Direito", 6, "DIR303", "Direito Penal I", 3, "08:00", "09:40", "Sala 401", "Prof. Roberto Campos"),
            ("Direito", 6, "DIR304", "Teoria Geral do Processo", 4, "10:00", "11:40", "Sala 403", "Prof. Thiago Moreira"),
            ("Direito", 2, "DIR301", "Direito Constitucional", 0, "10:00", "11:40", "Sala 404", "Prof. Eduardo Bastos"),
            ("Direito", 2, "DIR302", "Direito Civil I", 2, "10:00", "11:40", "Sala 404", "Profa. Luciana Torres"),
        ]
        for course, sem, code, name, dow, start, end, room, prof in schedule_data:
            h_s, m_s = map(int, start.split(":"))
            h_e, m_e = map(int, end.split(":"))
            db.add(ClassSchedule(
                tenant_id=tenant_id,
                course=course,
                semester=sem,
                subject_name=name,
                subject_code=code,
                day_of_week=dow,
                start_time=time(h_s, m_s),
                end_time=time(h_e, m_e),
                room=room,
                professor=prof,
                academic_period="2026.1",
            ))
        print(f"✓ {len(schedule_data)} horários de aula criados")

        # ══════════════════════════════════════════════════════════════════
        # 12. HOLERITES
        # ══════════════════════════════════════════════════════════════════
        salary_data = {
            "FUNC001": Decimal("3500.00"),
            "FUNC002": Decimal("5200.00"),
            "FUNC003": Decimal("6800.00"),
            "FUNC004": Decimal("2800.00"),
            "FUNC005": Decimal("7500.00"),
        }
        for emp in all_employees:
            gross = salary_data.get(emp.employee_number, Decimal("3000.00"))
            for month_num in range(1, 4):
                inss = round(gross * Decimal("0.11"), 2)
                irrf = round(gross * Decimal("0.075"), 2) if gross > Decimal("3000") else Decimal("0.00")
                vt = Decimal("220.00")
                va = Decimal("550.00")
                net = gross - inss - irrf - vt
                db.add(Payslip(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    reference_month=f"2026-{month_num:02d}",
                    gross_salary=gross,
                    net_salary=net,
                    deductions={
                        "INSS": str(inss), "IRRF": str(irrf),
                        "Vale Transporte": str(vt), "Vale Alimentação": str(va),
                    },
                ))
        print("✓ Holerites criados (jan-mar para todos)")

        # ══════════════════════════════════════════════════════════════════
        # 13. FÉRIAS
        # ══════════════════════════════════════════════════════════════════
        vacation_data = [
            (all_employees[0], 10, date(2025, 3, 1), date(2026, 2, 28)),
            (all_employees[1], 0, date(2025, 7, 1), date(2026, 6, 30)),
            (all_employees[2], 15, date(2025, 1, 10), date(2026, 1, 9)),
            (all_employees[3], 0, date(2025, 5, 20), date(2026, 5, 19)),
            (all_employees[4], 20, date(2024, 2, 1), date(2025, 1, 31)),
        ]
        for emp, used, start_date, end_date in vacation_data:
            db.add(VacationBalance(
                tenant_id=tenant_id,
                employee_id=emp.id,
                accrual_period_start=start_date,
                accrual_period_end=end_date,
                total_days=30,
                used_days=used,
                deadline_date=end_date + timedelta(days=365),
            ))
        print("✓ Saldos de férias criados")

        # ══════════════════════════════════════════════════════════════════
        # 14. REGISTROS DE PONTO
        # ══════════════════════════════════════════════════════════════════
        for emp in all_employees:
            for day_offset in range(10):  # Últimos 10 dias úteis
                rec_date = date(2026, 3, 16 + day_offset)
                if rec_date.weekday() >= 5:
                    continue
                db.add(TimeRecord(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    record_date=rec_date,
                    clock_in=datetime(rec_date.year, rec_date.month, rec_date.day, 8, 0, tzinfo=timezone.utc),
                    clock_out=datetime(rec_date.year, rec_date.month, rec_date.day, 17, 0, tzinfo=timezone.utc),
                    break_start=datetime(rec_date.year, rec_date.month, rec_date.day, 12, 0, tzinfo=timezone.utc),
                    break_end=datetime(rec_date.year, rec_date.month, rec_date.day, 13, 0, tzinfo=timezone.utc),
                    total_hours=Decimal("8.00"),
                    status="regular",
                ))
        print("✓ Registros de ponto criados (últimos 10 dias úteis)")

        # ══════════════════════════════════════════════════════════════════
        # 15. SOLICITAÇÕES RH
        # ══════════════════════════════════════════════════════════════════
        hr_requests = [
            (all_employees[0], "medical_cert", "Atestado médico - consulta odontológica dia 25/03", "approved", "Atestado registrado. 1 dia abonado."),
            (all_employees[1], "declaration", "Declaração de vínculo empregatício para financiamento", "approved", "Declaração emitida e enviada por e-mail."),
            (all_employees[2], "vacation", "Solicito férias de 15 dias a partir de 01/05/2026", "pending", None),
            (all_employees[3], "medical_cert", "Atestado médico - 2 dias (gripe)", "approved", "Atestado registrado. 2 dias abonados."),
            (all_employees[4], "declaration", "Comprovante de rendimentos 2025 para IR", "approved", "Documento enviado por e-mail corporativo."),
        ]
        for emp, req_type, desc, status, response in hr_requests:
            db.add(HRRequest(
                tenant_id=tenant_id,
                employee_id=emp.id,
                request_type=req_type,
                description=desc,
                status=status,
                response_text=response,
                responded_by=admin.id if status != "pending" else None,
                responded_at=NOW - timedelta(hours=2) if status != "pending" else None,
            ))
        print("✓ Solicitações RH criadas")

        # ══════════════════════════════════════════════════════════════════
        # 16. CONTATOS WHATSAPP
        # ══════════════════════════════════════════════════════════════════
        contacts = []
        # Contatos de alunos
        for student in all_students:
            contact = Contact(
                tenant_id=tenant_id,
                phone_number=student.phone,
                name=student.full_name,
                contact_type="student",
                student_id=student.id,
                is_verified=True,
            )
            db.add(contact)
            contacts.append(contact)

        # Contatos de funcionários
        for emp in all_employees:
            contact = Contact(
                tenant_id=tenant_id,
                phone_number=emp.phone,
                name=emp.full_name,
                contact_type="employee",
                employee_id=emp.id,
                is_verified=True,
            )
            db.add(contact)
            contacts.append(contact)

        # Contato não verificado (para demo)
        unverified = Contact(
            tenant_id=tenant_id,
            phone_number="+5511966660000",
            name="Visitante",
            contact_type="unknown",
            is_verified=False,
        )
        db.add(unverified)
        contacts.append(unverified)
        await db.flush()
        print(f"✓ {len(contacts)} contatos WhatsApp criados")

        # ══════════════════════════════════════════════════════════════════
        # 17. CONVERSAS + MENSAGENS
        # ══════════════════════════════════════════════════════════════════
        conversations_list = []

        # --- Conversa 1: Ana consulta notas ---
        conv1 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[0].id, channel="whatsapp",
            status="closed", context_type="student",
            started_at=NOW - timedelta(hours=5), last_message_at=NOW - timedelta(hours=4, minutes=45),
            closed_at=NOW - timedelta(hours=4, minutes=40), satisfaction_score=5,
        )
        db.add(conv1)
        await db.flush()
        conversations_list.append(conv1)

        msgs1 = [
            (conv1.id, "user", "Oi, quero ver minhas notas", "text", "grade_query", 0),
            (conv1.id, "bot", "Olá, Ana! 📚 Aqui estão suas notas do período 2026.1:\n\n📖 *Introdução à Administração*\n- P1: 8.50 ✅\n- P2: 7.00 ✅\n\n📖 *Contabilidade Básica*\n- P1: 9.00 ✅\n- P2: 6.50 ✅\n\n📖 *Matemática Financeira*\n- P1: 7.50 ✅\n- P2: 8.00 ✅\n\nParabéns! Todas aprovadas! 🎉", "text", "grade_query", 187),
            (conv1.id, "user", "Obrigada! E meu boleto de março?", "text", "boleto_query", 0),
            (conv1.id, "bot", "Aqui está seu boleto de março, Ana! 💰\n\n📄 *Ref: 2026-03*\n💵 Valor: R$ 1.250,00\n📅 Vencimento: 10/03/2026\n📊 Status: Pendente\n\n🔢 Código de barras:\n23793.38128 60000.0000012345 03000.000000 1 93260000125000\n\nPrecisa de mais alguma coisa?", "text", "boleto_query", 154),
            (conv1.id, "user", "Não, era isso. Valeu!", "text", "greeting", 0),
            (conv1.id, "bot", "Por nada, Ana! 😊 Bons estudos! Se precisar, é só chamar. 📚", "text", "greeting", 89),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs1:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        # --- Conversa 2: Bruno consulta horários ---
        conv2 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[1].id, channel="whatsapp",
            status="closed", context_type="student",
            started_at=NOW - timedelta(hours=3), last_message_at=NOW - timedelta(hours=2, minutes=50),
            closed_at=NOW - timedelta(hours=2, minutes=45), satisfaction_score=4,
        )
        db.add(conv2)
        await db.flush()
        conversations_list.append(conv2)

        msgs2 = [
            (conv2.id, "user", "Meus horários da semana", "text", "schedule_query", 0),
            (conv2.id, "bot", "Oi, Bruno! 📅 Aqui estão seus horários de Engenharia de Software (4º sem):\n\n🗓 *Segunda*: Algoritmos e E.D. — 19:00-20:40 — Lab 01\n🗓 *Terça*: Banco de Dados — 19:00-20:40 — Lab 02\n🗓 *Quarta*: Eng. de Requisitos — 21:00-22:40 — Sala 301\n🗓 *Quinta*: Programação Web — 19:00-20:40 — Lab 01\n\nPrecisa de mais alguma informação? 😊", "text", "schedule_query", 201),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs2:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        # --- Conversa 3: Maria (funcionária) consulta holerite ---
        conv3 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[8].id, channel="whatsapp",
            status="closed", context_type="employee",
            started_at=NOW - timedelta(hours=6), last_message_at=NOW - timedelta(hours=5, minutes=30),
            closed_at=NOW - timedelta(hours=5, minutes=25), satisfaction_score=5,
        )
        db.add(conv3)
        await db.flush()
        conversations_list.append(conv3)

        msgs3 = [
            (conv3.id, "user", "Preciso ver meu holerite", "text", "payslip_query", 0),
            (conv3.id, "bot", "Olá, Maria! 💼 Aqui estão seus últimos holerites:\n\n📄 *2026-03 (Março)*\n💰 Bruto: R$ 3.500,00\n📉 Descontos: INSS R$ 385,00 | IRRF R$ 262,50 | VT R$ 220,00\n💵 Líquido: R$ 2.632,50\n\n📄 *2026-02 (Fevereiro)*\n💵 Líquido: R$ 2.632,50\n\n📄 *2026-01 (Janeiro)*\n💵 Líquido: R$ 2.632,50\n\nPosso ajudar com mais alguma coisa?", "text", "payslip_query", 178),
            (conv3.id, "user", "Quero ver meu saldo de férias", "text", "vacation_query", 0),
            (conv3.id, "bot", "Aqui está seu saldo de férias, Maria! 🏖️\n\n📋 *Período aquisitivo*: 01/03/2025 a 28/02/2026\n✅ Dias totais: 30\n🏖️ Dias usados: 10\n📊 Dias restantes: 20\n📅 Prazo limite: 28/02/2027\n\nDeseja solicitar férias? É só me dizer! 😊", "text", "vacation_query", 143),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs3:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        # --- Conversa 4: Diego pede atendente (ticket) ---
        conv4 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[3].id, channel="whatsapp",
            status="waiting_agent", context_type="student",
            started_at=NOW - timedelta(hours=1), last_message_at=NOW - timedelta(minutes=55),
            assigned_agent_id=agent1.id,
        )
        db.add(conv4)
        await db.flush()
        conversations_list.append(conv4)

        msgs4 = [
            (conv4.id, "user", "Quero falar com um atendente sobre meu recurso de nota", "text", "human_handoff", 0),
            (conv4.id, "bot", "Entendido! 🙋 Vou te transferir para um de nossos atendentes.\nUm ticket foi aberto com o protocolo *TKT-2026-0001*.\nEm breve entraremos em contato. Obrigado pela paciência! 🙏", "text", "human_handoff", 0),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs4:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        # --- Conversa 5: Carlos (func) consulta ponto ---
        conv5 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[9].id, channel="whatsapp",
            status="closed", context_type="employee",
            started_at=NOW - timedelta(hours=2), last_message_at=NOW - timedelta(hours=1, minutes=45),
            closed_at=NOW - timedelta(hours=1, minutes=40), satisfaction_score=4,
        )
        db.add(conv5)
        await db.flush()
        conversations_list.append(conv5)

        msgs5 = [
            (conv5.id, "user", "Quero ver meu registro de ponto da semana", "text", "time_record_query", 0),
            (conv5.id, "bot", "Olá, Carlos! ⏰ Aqui estão seus registros de ponto desta semana:\n\n📅 Seg 23/03: 08:00→17:00 (8h) ✅\n📅 Ter 24/03: 08:00→17:00 (8h) ✅\n📅 Qua 25/03: 08:00→17:00 (8h) ✅\n📅 Qui 26/03: 08:00→17:00 (8h) ✅\n📅 Sex 27/03: 08:00→17:00 (8h) ✅\n\n✅ Todos os registros regulares. Total da semana: 40h.\nPrecisa de mais alguma coisa?", "text", "time_record_query", 165),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs5:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        # --- Conversa 6: Elena consulta frequência ---
        conv6 = Conversation(
            tenant_id=tenant_id, contact_id=contacts[4].id, channel="whatsapp",
            status="active", context_type="student",
            started_at=NOW - timedelta(minutes=30), last_message_at=NOW - timedelta(minutes=25),
        )
        db.add(conv6)
        await db.flush()
        conversations_list.append(conv6)

        msgs6 = [
            (conv6.id, "user", "Minha frequência tá como?", "text", "attendance_query", 0),
            (conv6.id, "bot", "Olá, Elena! 📊 Sua frequência em Administração (4º sem):\n\n📚 Marketing I — 35/40 aulas (12.5% faltas) ✅\n📚 Introdução à Administração — 37/40 aulas (7.5% faltas) ✅\n📚 Contabilidade — 33/40 aulas (17.5% faltas) ⚠️\n📚 Matemática Financeira — 38/40 aulas (5% faltas) ✅\n\n⚠️ Atenção: Contabilidade está próximo do limite de 25% de faltas. Cuide da frequência!\n\nDúvidas? É só perguntar! 😊", "text", "attendance_query", 198),
        ]
        for conv_id, sender, content, msg_type, intent, tokens in msgs6:
            db.add(Message(
                tenant_id=tenant_id, conversation_id=conv_id, sender_type=sender,
                content=content, message_type=msg_type, intent=intent,
                ai_tokens_used=tokens if tokens else None,
                is_delivered=True, is_read=True,
            ))

        print(f"✓ {len(conversations_list)} conversas com mensagens criadas")

        # ══════════════════════════════════════════════════════════════════
        # 18. TICKETS
        # ══════════════════════════════════════════════════════════════════
        tickets_data = [
            ("TKT-2026-0001", "Recurso de nota - Direito Constitucional",
             "Aluno Diego Santos solicita revisão da prova P1 de Direito Constitucional. Nota atual: 5.50.",
             "high", "in_progress", contacts[3].id, conv4.id, agent1.id, "Acadêmico"),
            ("TKT-2026-0002", "2ª via de diploma",
             "Aluna Carla Mendes solicita 2ª via do diploma de curso anterior.",
             "medium", "open", contacts[2].id, None, None, "Documentação"),
            ("TKT-2026-0003", "Problema com boleto duplicado",
             "Aluno Felipe Almeida reporta boleto duplicado para o mês 03/2026.",
             "high", "resolved", contacts[5].id, None, agent2.id, "Financeiro"),
            ("TKT-2026-0004", "Solicitação de declaração de vínculo",
             "Funcionária Fernanda Costa solicita declaração de vínculo empregatício para financiamento.",
             "low", "closed", contacts[10].id, None, agent1.id, "RH"),
            ("TKT-2026-0005", "Erro no sistema de ponto",
             "Funcionário Roberto relata que ponto de 20/03 não foi registrado corretamente.",
             "critical", "in_progress", contacts[11].id, None, agent2.id, "TI"),
        ]
        all_tickets = []
        for protocol, subject, desc, priority, status, contact_id, conv_id_t, assigned, category in tickets_data:
            t = Ticket(
                tenant_id=tenant_id,
                protocol_number=protocol,
                contact_id=contact_id,
                conversation_id=conv_id_t,
                subject=subject,
                description=desc,
                priority=priority,
                status=status,
                assigned_to=assigned,
                category=category,
                sla_deadline=NOW + timedelta(hours=4) if status in ("open", "in_progress") else None,
                resolved_at=NOW - timedelta(hours=1) if status in ("resolved", "closed") else None,
            )
            db.add(t)
            all_tickets.append(t)
        await db.flush()

        # Comentários em tickets
        comments = [
            (all_tickets[0], agent1.id, "Prova localizada. Aguardando professor para revisão.", False),
            (all_tickets[0], admin.id, "Professor Eduardo Bastos confirmou que revisará até 02/04.", True),
            (all_tickets[2], agent2.id, "Boleto duplicado identificado e cancelado. Novo boleto gerado.", False),
            (all_tickets[2], agent2.id, "Aluno confirmou recebimento do novo boleto.", False),
            (all_tickets[4], agent2.id, "Verificando logs do sistema de ponto. Possível falha no servidor.", True),
        ]
        for ticket, author, content, internal in comments:
            db.add(TicketComment(
                ticket_id=ticket.id,
                author_id=author,
                content=content,
                is_internal=internal,
            ))
        print(f"✓ {len(all_tickets)} tickets com comentários criados")

        # ══════════════════════════════════════════════════════════════════
        # 19. SLIDE TEMPLATES + APRESENTAÇÕES
        # ══════════════════════════════════════════════════════════════════
        template_anchieta = SlideTemplate(
            tenant_id=tenant_id,
            name="Padrão Anchieta",
            description="Template oficial da Faculdade Anchieta com cores e fontes institucionais",
            template_rules={
                "colors": {
                    "primary": "#1B3A5C",
                    "secondary": "#E8B931",
                    "background": "#FFFFFF",
                    "text": "#333333",
                    "accent": "#2E86AB",
                },
                "fonts": {
                    "title": "Montserrat Bold",
                    "body": "Open Sans",
                    "size_title": 32,
                    "size_body": 18,
                    "size_caption": 14,
                },
                "layout": {
                    "logo_position": "top-right",
                    "footer_text": "Faculdade Anchieta — Educação que transforma",
                    "max_bullets_per_slide": 6,
                    "include_slide_numbers": True,
                    "aspect_ratio": "16:9",
                },
            },
            example_content="Slide de capa sempre com título da aula, disciplina, professor e data. Usar azul (#1B3A5C) no fundo da capa.",
            is_default=True,
        )
        template_minimal = SlideTemplate(
            tenant_id=tenant_id,
            name="Minimalista",
            description="Template limpo e moderno para workshops e seminários",
            template_rules={
                "colors": {
                    "primary": "#2C3E50",
                    "secondary": "#3498DB",
                    "background": "#FAFAFA",
                    "text": "#2C3E50",
                },
                "fonts": {
                    "title": "Roboto Bold",
                    "body": "Roboto Light",
                    "size_title": 36,
                    "size_body": 20,
                },
                "layout": {
                    "logo_position": "bottom-left",
                    "footer_text": "",
                    "max_bullets_per_slide": 4,
                    "include_slide_numbers": False,
                },
            },
            is_default=False,
        )
        db.add_all([template_anchieta, template_minimal])
        await db.flush()

        # Apresentações de exemplo
        pres1 = SlidePresentation(
            tenant_id=tenant_id,
            teacher_id=teacher1.id,
            template_id=template_anchieta.id,
            title="Algoritmos de Ordenação",
            subject="Algoritmos e Estrutura de Dados",
            prompt_used="Crie uma aula sobre algoritmos de ordenação (bubble sort, merge sort, quick sort) para o 4º semestre de Engenharia de Software, com exemplos práticos em Python",
            slides_content=[
                {"slide_number": 1, "title": "Algoritmos de Ordenação", "content": ["Disciplina: Algoritmos e Estrutura de Dados", "Prof. André Silva", "4º Semestre — 2026.1"], "notes": "Apresentar tema e objetivos da aula", "layout": "title"},
                {"slide_number": 2, "title": "O que é Ordenação?", "content": ["Processo de reorganizar dados em uma sequência específica", "Aplicações: bancos de dados, busca binária, interfaces de usuário", "Critérios: tempo, espaço, estabilidade", "Big-O: como medimos eficiência"], "notes": "Enfatizar que ordenação é base para muitos algoritmos", "layout": "default"},
                {"slide_number": 3, "title": "Bubble Sort", "content": ["Compara elementos adjacentes e troca se necessário", "Complexidade: O(n²) — pior e médio caso", "Estável e in-place", "Simples mas ineficiente para grandes volumes"], "notes": "Demonstrar com exemplo visual no quadro", "layout": "default"},
                {"slide_number": 4, "title": "Bubble Sort — Exemplo Python", "content": ["def bubble_sort(arr):", "    for i in range(len(arr)):", "        for j in range(0, len(arr)-i-1):", "            if arr[j] > arr[j+1]:", "                arr[j], arr[j+1] = arr[j+1], arr[j]"], "notes": "Pedir aos alunos que identifiquem a complexidade", "layout": "default"},
                {"slide_number": 5, "title": "Merge Sort", "content": ["Divide e conquista: divide o array ao meio recursivamente", "Complexidade: O(n log n) — todos os casos", "Estável, mas usa memória extra O(n)", "Ideal para grandes volumes de dados"], "notes": "Usar diagrama de árvore para demonstrar divisões", "layout": "default"},
                {"slide_number": 6, "title": "Quick Sort", "content": ["Escolhe um pivô e particiona o array", "Complexidade: O(n log n) médio, O(n²) pior caso", "In-place (usa pouca memória extra)", "Na prática, mais rápido que Merge Sort"], "notes": "Discutir escolha de pivô e seu impacto", "layout": "default"},
                {"slide_number": 7, "title": "Comparação de Algoritmos", "content": ["Bubble Sort: O(n²) | Estável | In-place", "Merge Sort: O(n log n) | Estável | O(n) extra", "Quick Sort: O(n log n)* | Instável | In-place"], "notes": "Usar tabela comparativa", "layout": "two_columns"},
                {"slide_number": 8, "title": "Resumo e Referências", "content": ["Ordenação é fundamental para eficiência de software", "Escolha do algoritmo depende do contexto", "Referência: Cormen — Introduction to Algorithms, Cap. 2 e 7", "Exercício: implementar os 3 algoritmos e comparar tempos"], "notes": "Propor exercício prático para próxima aula", "layout": "default"},
            ],
            status="final",
            version=2,
            total_slides=8,
        )
        db.add(pres1)
        await db.flush()

        pres2 = SlidePresentation(
            tenant_id=tenant_id,
            teacher_id=teacher2.id,
            template_id=template_anchieta.id,
            title="Modelagem de Banco de Dados Relacional",
            subject="Banco de Dados",
            prompt_used="Crie uma aula sobre modelagem de banco de dados relacional com MER e normalização para alunos do 4º semestre",
            slides_content=[
                {"slide_number": 1, "title": "Modelagem de Banco de Dados Relacional", "content": ["Disciplina: Banco de Dados", "Profa. Julia Santos", "4º Semestre — 2026.1"], "notes": "Introdução ao tema", "layout": "title"},
                {"slide_number": 2, "title": "Por que Modelar?", "content": ["Evitar redundância de dados", "Garantir integridade referencial", "Facilitar manutenção e evolução", "Base para um sistema eficiente"], "notes": "Dar exemplos de sistemas com modelagem ruim", "layout": "default"},
                {"slide_number": 3, "title": "Modelo Entidade-Relacionamento", "content": ["Entidades: objetos do mundo real", "Atributos: propriedades das entidades", "Relacionamentos: associações entre entidades", "Cardinalidade: 1:1, 1:N, N:M"], "notes": "Usar exemplo de sistema escolar como referência", "layout": "default"},
                {"slide_number": 4, "title": "Normalização", "content": ["1FN: eliminar grupos repetitivos", "2FN: dependência funcional total", "3FN: eliminar dependências transitivas", "BCNF: todo determinante é chave candidata"], "notes": "Demonstrar cada forma normal com exemplo prático", "layout": "default"},
                {"slide_number": 5, "title": "Referências", "content": ["Elmasri & Navathe — Banco de Dados, 7ª ed.", "Date, C.J. — Introdução a Sistemas de BD", "Exercício: modelar sistema de biblioteca"], "notes": "Propor exercício individual", "layout": "default"},
            ],
            status="draft",
            version=1,
            total_slides=5,
        )
        db.add(pres2)
        await db.flush()

        pres3 = SlidePresentation(
            tenant_id=tenant_id,
            teacher_id=teacher3.id,
            template_id=template_anchieta.id,
            title="Fundamentos de Didática — Planejamento de Aula",
            subject="Didática Geral",
            prompt_used="Crie uma aula sobre planejamento didático e técnicas de ensino para alunos de Pedagogia",
            slides_content=[
                {"slide_number": 1, "title": "Planejamento de Aula", "content": ["Disciplina: Didática Geral", "Profa. Ana Beatriz", "1º Semestre — 2026.1"], "notes": "", "layout": "title"},
                {"slide_number": 2, "title": "Por que Planejar?", "content": ["Organização do tempo e conteúdo", "Alinhamento com objetivos de aprendizagem", "Adaptação às necessidades dos alunos", "Avaliação como parte do planejamento"], "notes": "Debate: já tiveram aulas sem planejamento?", "layout": "default"},
                {"slide_number": 3, "title": "Elementos do Plano de Aula", "content": ["Objetivos (geral e específicos)", "Conteúdo programático", "Metodologia e recursos", "Avaliação e feedback"], "notes": "Distribuir modelo de plano de aula", "layout": "default"},
                {"slide_number": 4, "title": "Metodologias Ativas", "content": ["Sala de aula invertida", "Aprendizagem baseada em projetos", "Gamificação", "Estudo de caso e debates"], "notes": "Exemplificar cada metodologia", "layout": "two_columns"},
                {"slide_number": 5, "title": "Resumo", "content": ["Planejar é fundamental para ensino eficaz", "Metodologias ativas aumentam engajamento", "Exercício: elaborar plano de aula para 5º ano", "Leitura: Libâneo — Didática, Cap. 5-7"], "notes": "", "layout": "default"},
            ],
            status="final",
            version=1,
            total_slides=5,
        )
        db.add(pres3)
        await db.flush()

        # Logs de geração
        for pres, action_count in [(pres1, 2), (pres2, 1), (pres3, 1)]:
            for i in range(action_count):
                db.add(SlideGenerationLog(
                    tenant_id=tenant_id,
                    teacher_id=pres.teacher_id,
                    presentation_id=pres.id,
                    prompt=pres.prompt_used if i == 0 else "Adicione mais exemplos de código nos slides 4 e 6",
                    action="create" if i == 0 else "update",
                    tokens_used=1250 + i * 300,
                    ai_provider="groq",
                ))
        print("✓ 2 templates de slides + 3 apresentações com logs criados")

        # ══════════════════════════════════════════════════════════════════
        # 20. TEMPLATES DE MENSAGEM (WhatsApp HSM)
        # ══════════════════════════════════════════════════════════════════
        msg_templates = [
            MessageTemplate(
                tenant_id=tenant_id,
                name="Lembrete de Boleto",
                meta_template_name="boleto_reminder",
                language_code="pt_BR",
                category="UTILITY",
                parameters_schema={"body": ["nome", "valor", "vencimento"]},
                is_active=True,
            ),
            MessageTemplate(
                tenant_id=tenant_id,
                name="Notificação de Nota",
                meta_template_name="grade_notification",
                language_code="pt_BR",
                category="UTILITY",
                parameters_schema={"body": ["nome", "disciplina", "nota"]},
                is_active=True,
            ),
            MessageTemplate(
                tenant_id=tenant_id,
                name="Convite para Evento",
                meta_template_name="event_invite",
                language_code="pt_BR",
                category="MARKETING",
                parameters_schema={"body": ["nome", "evento", "data", "local"]},
                is_active=True,
            ),
            MessageTemplate(
                tenant_id=tenant_id,
                name="Pesquisa de Satisfação",
                meta_template_name="satisfaction_survey",
                language_code="pt_BR",
                category="UTILITY",
                parameters_schema={"body": ["nome"]},
                is_active=True,
            ),
        ]
        db.add_all(msg_templates)
        await db.flush()
        print("✓ 4 templates de mensagem criados")

        # ══════════════════════════════════════════════════════════════════
        # 21. PESQUISAS DE SATISFAÇÃO
        # ══════════════════════════════════════════════════════════════════
        surveys = [
            SatisfactionSurvey(
                tenant_id=tenant_id,
                conversation_id=conv1.id,
                contact_id=contacts[0].id,
                score=5,
                feedback_text="Muito rápido e preciso! Adorei poder ver minhas notas pelo WhatsApp.",
                responder_type="bot",
                survey_sent_at=NOW - timedelta(hours=4, minutes=38),
                responded_at=NOW - timedelta(hours=4, minutes=35),
            ),
            SatisfactionSurvey(
                tenant_id=tenant_id,
                conversation_id=conv2.id,
                contact_id=contacts[1].id,
                score=4,
                feedback_text="Funciona bem, mas queria ver o mapa da sala também.",
                responder_type="bot",
                survey_sent_at=NOW - timedelta(hours=2, minutes=43),
                responded_at=NOW - timedelta(hours=2, minutes=40),
            ),
            SatisfactionSurvey(
                tenant_id=tenant_id,
                conversation_id=conv3.id,
                contact_id=contacts[8].id,
                score=5,
                feedback_text="Excelente! Antes tinha que ir na sala do RH, agora é tudo pelo celular.",
                responder_type="bot",
                survey_sent_at=NOW - timedelta(hours=5, minutes=23),
                responded_at=NOW - timedelta(hours=5, minutes=18),
            ),
            SatisfactionSurvey(
                tenant_id=tenant_id,
                conversation_id=conv5.id,
                contact_id=contacts[9].id,
                score=4,
                feedback_text="Prático! Consegui ver meu ponto rapidamente.",
                responder_type="bot",
                survey_sent_at=NOW - timedelta(hours=1, minutes=38),
                responded_at=NOW - timedelta(hours=1, minutes=32),
            ),
        ]
        db.add_all(surveys)
        print("✓ 4 pesquisas de satisfação criadas (média: 4.5/5)")

        # ══════════════════════════════════════════════════════════════════
        # 22. RESOLUÇÕES (APRENDIZADO IA)
        # ══════════════════════════════════════════════════════════════════
        resolutions = [
            TicketResolution(
                tenant_id=tenant_id,
                ticket_id=all_tickets[2].id,
                problem_category="billing",
                problem_description="Aluno reportou boleto duplicado para o mesmo mês de referência",
                resolution_description="Identificado boleto duplicado no sistema. Cancelado o boleto mais recente e mantido o original. Aluno confirmou resolução.",
                resolution_type="human",
                satisfaction_score=5,
            ),
            TicketResolution(
                tenant_id=tenant_id,
                ticket_id=all_tickets[3].id,
                problem_category="hr_documents",
                problem_description="Funcionária solicitou declaração de vínculo empregatício para financiamento imobiliário",
                resolution_description="Declaração gerada pelo sistema de RH com dados atualizados. Enviada por e-mail e cópia física entregue na secretaria.",
                resolution_type="human",
                satisfaction_score=5,
            ),
        ]
        db.add_all(resolutions)
        print("✓ 2 resoluções de aprendizado IA criadas")

        # ══════════════════════════════════════════════════════════════════
        # 23. MÉTRICAS DE RESPOSTA
        # ══════════════════════════════════════════════════════════════════
        # Buscar mensagens de bot para vincular métricas
        bot_msgs_result = await db.execute(
            select(Message).where(
                Message.tenant_id == tenant_id,
                Message.sender_type == "bot",
            ).limit(6)
        )
        bot_msgs = bot_msgs_result.scalars().all()
        for i, msg in enumerate(bot_msgs):
            db.add(ResponseTimeMetric(
                tenant_id=tenant_id,
                conversation_id=msg.conversation_id,
                message_id=msg.id,
                responder_type="bot",
                response_time_seconds=float(1.2 + i * 0.3),
            ))
        print(f"✓ {len(bot_msgs)} métricas de tempo de resposta criadas")

        # ══════════════════════════════════════════════════════════════════
        # 24. AUDIT LOG
        # ══════════════════════════════════════════════════════════════════
        audit_entries = [
            AuditLog(tenant_id=tenant_id, user_id=admin.id, action="login", entity_type="auth", details={"ip": "192.168.1.100"}),
            AuditLog(tenant_id=tenant_id, user_id=admin.id, action="create", entity_type="user", entity_id=teacher1.id, details={"role": "teacher"}),
            AuditLog(tenant_id=tenant_id, user_id=agent1.id, action="update", entity_type="ticket", entity_id=all_tickets[0].id, details={"status": "in_progress"}),
            AuditLog(tenant_id=tenant_id, user_id=agent2.id, action="update", entity_type="ticket", entity_id=all_tickets[2].id, details={"status": "resolved"}),
        ]
        db.add_all(audit_entries)
        print("✓ Log de auditoria criado")

        # ══════════════════════════════════════════════════════════════════
        # COMMIT
        # ══════════════════════════════════════════════════════════════════
        await db.commit()
        print("\n" + "=" * 60)
        print("✅ SEED DEMO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📊 Resumo dos dados criados:")
        print(f"   👤 Usuários: 1 admin, 2 agentes, 3 professores")
        print(f"   🎓 Alunos: {len(all_students)}")
        print(f"   👔 Funcionários: {len(all_employees)}")
        print(f"   📱 Contatos WhatsApp: {len(contacts)}")
        print(f"   💬 Conversas: {len(conversations_list)}")
        print(f"   🎫 Tickets: {len(all_tickets)}")
        print(f"   📊 Apresentações de Slides: 3")
        print(f"   📝 Templates de Slides: 2")
        print(f"   📚 Artigos KB: 14")
        print(f"   ⭐ Pesquisas de Satisfação: 4 (média 4.5/5)")
        print(f"   📧 Templates de Mensagem: 4")
        print(f"\n📋 Credenciais:")
        print(f"   Super Admin: {settings.SUPER_ADMIN_EMAIL} / {settings.SUPER_ADMIN_PASSWORD}")
        print(f"   Admin: gestor@anchieta.edu.br / Gestor@2026")
        print(f"   Agente: suporte1@anchieta.edu.br / Suporte@2026")
        print(f"   Professor: prof.andre@anchieta.edu.br / Prof@2026")
        print(f"\n🚀 API: http://localhost:8000/docs")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo())
