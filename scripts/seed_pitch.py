"""
Seed para PITCH DECK — dados realistas para demonstração de vendas.

Cria cenários reais de atendimento:
- 5 alunos (ativo, inadimplente, trancado) com notas, frequência, boletos, horários
- 3 funcionários (professor, RH, secretaria) com holerites, férias, ponto
- CPFs mockados para autenticação por senha (últimos 6 dígitos)

Uso: docker exec -it igs_api python scripts/seed_pitch.py
  ou: python scripts/seed_pitch.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.billing import Boleto
from app.models.employee import Employee, HRRequest, Payslip, TimeRecord, VacationBalance
from app.models.schedule import ClassSchedule
from app.models.student import AttendanceRecord, Grade, Student
from app.models.tenant import Tenant


async def seed_pitch():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Buscar tenant Anchieta
        result = await db.execute(select(Tenant).where(Tenant.slug == "anchieta"))
        tenant = result.scalar_one_or_none()
        if not tenant:
            print("ERRO: Tenant 'anchieta' não encontrado. Rode seed_demo.py primeiro.")
            return

        tenant_id = tenant.id
        print(f"Tenant: {tenant.name} ({tenant_id})")

        # ══════════════════════════════════════════════════════════════════
        # Limpar dados antigos de students/employees deste tenant
        # ══════════════════════════════════════════════════════════════════
        # Deletar em ordem reversa de dependência
        for model in [
            Grade, AttendanceRecord, Boleto, ClassSchedule,
            Payslip, VacationBalance, TimeRecord, HRRequest,
        ]:
            await db.execute(delete(model).where(model.tenant_id == tenant_id))

        await db.execute(delete(Student).where(Student.tenant_id == tenant_id))
        await db.execute(delete(Employee).where(Employee.tenant_id == tenant_id))
        await db.flush()
        print("Dados antigos limpos.")

        # ══════════════════════════════════════════════════════════════════
        # ALUNOS
        # ══════════════════════════════════════════════════════════════════
        students_raw = [
            {
                "ra": "20241001",
                "name": "Lucas Oliveira Silva",
                "cpf": "52938471620",
                "email": "lucas.silva@edu.anchieta.br",
                "phone": "+5511991001001",
                "course": "Engenharia de Software",
                "semester": 4,
                "status": "active",
            },
            {
                "ra": "20241002",
                "name": "Mariana Costa Santos",
                "cpf": "61827394051",
                "email": "mariana.santos@edu.anchieta.br",
                "phone": "+5511991002002",
                "course": "Direito",
                "semester": 6,
                "status": "active",  # terá boleto vencido
            },
            {
                "ra": "20241003",
                "name": "Beatriz Fernandes Lima",
                "cpf": "73948261530",
                "email": "beatriz.lima@edu.anchieta.br",
                "phone": "+5511991003003",
                "course": "Enfermagem",
                "semester": 2,
                "status": "active",
            },
            {
                "ra": "20241004",
                "name": "Rafael Mendes Pereira",
                "cpf": "84059372641",
                "email": "rafael.pereira@edu.anchieta.br",
                "phone": "+5511991004004",
                "course": "Administração",
                "semester": 5,
                "status": "locked",
            },
            {
                "ra": "20241005",
                "name": "Camila Rodrigues Alves",
                "cpf": "95160483752",
                "email": "camila.alves@edu.anchieta.br",
                "phone": "+5511991005005",
                "course": "Psicologia",
                "semester": 3,
                "status": "active",
            },
        ]

        students = []
        for s in students_raw:
            student = Student(
                tenant_id=tenant_id,
                registration_number=s["ra"],
                full_name=s["name"],
                cpf=s["cpf"],
                email=s["email"],
                phone=s["phone"],
                course=s["course"],
                semester=s["semester"],
                enrollment_status=s["status"],
                enrollment_date=date(2024, 2, 1),
            )
            db.add(student)
            students.append(student)
        await db.flush()
        print(f"{len(students)} alunos criados")

        # Mapa por nome para fácil referência
        lucas, mariana, beatriz, rafael, camila = students

        # ══════════════════════════════════════════════════════════════════
        # NOTAS
        # ══════════════════════════════════════════════════════════════════
        grades_data = [
            # Lucas — Eng. Software 4º sem
            (lucas, "Banco de Dados", "BD201", "2026.1", "P1", Decimal("8.5"), "approved"),
            (lucas, "Banco de Dados", "BD201", "2026.1", "P2", Decimal("7.0"), "approved"),
            (lucas, "Engenharia de Software", "ES301", "2026.1", "P1", Decimal("9.0"), "approved"),
            (lucas, "Engenharia de Software", "ES301", "2026.1", "P2", Decimal("8.5"), "approved"),
            (lucas, "Estrutura de Dados", "ED202", "2026.1", "P1", Decimal("6.5"), "pending"),
            (lucas, "Estrutura de Dados", "ED202", "2026.1", "P2", Decimal("7.5"), "approved"),
            (lucas, "Cálculo III", "MT301", "2026.1", "P1", Decimal("5.0"), "pending"),
            (lucas, "Cálculo III", "MT301", "2026.1", "P2", Decimal("6.0"), "pending"),
            (lucas, "Redes de Computadores", "RC201", "2026.1", "P1", Decimal("7.5"), "approved"),
            # Mariana — Direito 6º sem
            (mariana, "Direito Civil IV", "DC401", "2026.1", "P1", Decimal("7.0"), "approved"),
            (mariana, "Direito Civil IV", "DC401", "2026.1", "P2", Decimal("6.5"), "approved"),
            (mariana, "Direito Penal III", "DP301", "2026.1", "P1", Decimal("8.0"), "approved"),
            (mariana, "Direito Constitucional", "DCO201", "2026.1", "P1", Decimal("9.5"), "approved"),
            (mariana, "Processo Civil", "PC301", "2026.1", "P1", Decimal("4.5"), "pending"),
            # Beatriz — Enfermagem 2º sem
            (beatriz, "Anatomia Humana", "AH101", "2026.1", "P1", Decimal("9.0"), "approved"),
            (beatriz, "Anatomia Humana", "AH101", "2026.1", "P2", Decimal("9.5"), "approved"),
            (beatriz, "Bioquímica", "BQ101", "2026.1", "P1", Decimal("8.0"), "approved"),
            (beatriz, "Farmacologia", "FM101", "2026.1", "P1", Decimal("7.5"), "approved"),
            # Camila — Psicologia 3º sem
            (camila, "Psicologia Social", "PS201", "2026.1", "P1", Decimal("8.5"), "approved"),
            (camila, "Psicologia Social", "PS201", "2026.1", "P2", Decimal("9.0"), "approved"),
            (camila, "Neurociência", "NC201", "2026.1", "P1", Decimal("7.0"), "approved"),
            (camila, "Psicopatologia", "PP201", "2026.1", "P1", Decimal("6.0"), "pending"),
        ]

        for student, subject, code, period, gtype, value, status in grades_data:
            db.add(Grade(
                tenant_id=tenant_id,
                student_id=student.id,
                subject_name=subject,
                subject_code=code,
                academic_period=period,
                grade_type=gtype,
                grade_value=value,
                status=status,
            ))
        await db.flush()
        print(f"{len(grades_data)} notas criadas")

        # ══════════════════════════════════════════════════════════════════
        # FREQUÊNCIA
        # ══════════════════════════════════════════════════════════════════
        attendance_data = [
            # Lucas
            (lucas, "Banco de Dados", "BD201", 40, 36, Decimal("10.0")),
            (lucas, "Engenharia de Software", "ES301", 40, 38, Decimal("5.0")),
            (lucas, "Estrutura de Dados", "ED202", 40, 30, Decimal("25.0")),
            (lucas, "Cálculo III", "MT301", 40, 28, Decimal("30.0")),
            (lucas, "Redes de Computadores", "RC201", 40, 37, Decimal("7.5")),
            # Mariana
            (mariana, "Direito Civil IV", "DC401", 40, 39, Decimal("2.5")),
            (mariana, "Direito Penal III", "DP301", 40, 35, Decimal("12.5")),
            (mariana, "Direito Constitucional", "DCO201", 40, 40, Decimal("0.0")),
            (mariana, "Processo Civil", "PC301", 40, 32, Decimal("20.0")),
            # Beatriz
            (beatriz, "Anatomia Humana", "AH101", 40, 40, Decimal("0.0")),
            (beatriz, "Bioquímica", "BQ101", 40, 38, Decimal("5.0")),
            (beatriz, "Farmacologia", "FM101", 40, 39, Decimal("2.5")),
            # Camila
            (camila, "Psicologia Social", "PS201", 40, 36, Decimal("10.0")),
            (camila, "Neurociência", "NC201", 40, 34, Decimal("15.0")),
            (camila, "Psicopatologia", "PP201", 40, 31, Decimal("22.5")),
        ]

        for student, subject, code, total, attended, absence in attendance_data:
            db.add(AttendanceRecord(
                tenant_id=tenant_id,
                student_id=student.id,
                subject_name=subject,
                subject_code=code,
                academic_period="2026.1",
                total_classes=total,
                attended=attended,
                absence_pct=absence,
            ))
        await db.flush()
        print(f"{len(attendance_data)} registros de frequência criados")

        # ══════════════════════════════════════════════════════════════════
        # BOLETOS
        # ══════════════════════════════════════════════════════════════════
        today = date.today()
        boletos_data = []

        # Lucas — tudo em dia
        for month in range(1, 5):
            boletos_data.append((
                lucas, f"2026-{month:02d}", Decimal("1890.00"),
                date(2026, month, 10),
                "paid" if month <= 3 else "pending",
            ))

        # Mariana — boleto de fevereiro VENCIDO (inadimplente)
        for month in range(1, 5):
            status = "paid" if month == 1 else ("overdue" if month == 2 else "pending")
            boletos_data.append((
                mariana, f"2026-{month:02d}", Decimal("2150.00"),
                date(2026, month, 10),
                status,
            ))

        # Beatriz — tudo em dia
        for month in range(1, 5):
            boletos_data.append((
                beatriz, f"2026-{month:02d}", Decimal("1650.00"),
                date(2026, month, 10),
                "paid" if month <= 3 else "pending",
            ))

        # Rafael — trancado, sem boletos recentes
        boletos_data.append((
            rafael, "2026-01", Decimal("1450.00"), date(2026, 1, 10), "paid",
        ))

        # Camila — tudo em dia
        for month in range(1, 5):
            boletos_data.append((
                camila, f"2026-{month:02d}", Decimal("1750.00"),
                date(2026, month, 10),
                "paid" if month <= 3 else "pending",
            ))

        for student, ref_month, amount, due, status in boletos_data:
            db.add(Boleto(
                tenant_id=tenant_id,
                student_id=student.id,
                reference_month=ref_month,
                amount=amount,
                due_date=due,
                status=status,
                barcode=f"23793.38128 60000.{student.registration_number} 1 92260000{int(amount*100):08d}",
            ))
        await db.flush()
        print(f"{len(boletos_data)} boletos criados")

        # ══════════════════════════════════════════════════════════════════
        # HORÁRIOS — Eng. Software 4º sem (Lucas)
        # ══════════════════════════════════════════════════════════════════
        schedules_data = [
            (0, "Banco de Dados", "BD201", time(19, 0), time(20, 40), "Lab 3", "Prof. Ricardo Souza"),
            (0, "Redes de Computadores", "RC201", time(21, 0), time(22, 40), "Sala 205", "Prof. Marcos Lima"),
            (1, "Engenharia de Software", "ES301", time(19, 0), time(20, 40), "Sala 301", "Prof. André Moreira"),
            (1, "Estrutura de Dados", "ED202", time(21, 0), time(22, 40), "Lab 2", "Prof. Carla Ribeiro"),
            (2, "Cálculo III", "MT301", time(19, 0), time(20, 40), "Sala 102", "Prof. Helena Castro"),
            (2, "Banco de Dados", "BD201", time(21, 0), time(22, 40), "Lab 3", "Prof. Ricardo Souza"),
            (3, "Engenharia de Software", "ES301", time(19, 0), time(20, 40), "Sala 301", "Prof. André Moreira"),
            (3, "Redes de Computadores", "RC201", time(21, 0), time(22, 40), "Sala 205", "Prof. Marcos Lima"),
            (4, "Estrutura de Dados", "ED202", time(19, 0), time(20, 40), "Lab 2", "Prof. Carla Ribeiro"),
            (4, "Cálculo III", "MT301", time(21, 0), time(22, 40), "Sala 102", "Prof. Helena Castro"),
        ]

        for day, subject, code, start, end, room, prof in schedules_data:
            db.add(ClassSchedule(
                tenant_id=tenant_id,
                course="Engenharia de Software",
                semester=4,
                subject_name=subject,
                subject_code=code,
                day_of_week=day,
                start_time=start,
                end_time=end,
                room=room,
                professor=prof,
                academic_period="2026.1",
            ))
        await db.flush()
        print(f"{len(schedules_data)} horários criados")

        # ══════════════════════════════════════════════════════════════════
        # FUNCIONÁRIOS
        # ══════════════════════════════════════════════════════════════════
        employees_raw = [
            {
                "number": "FUNC001",
                "name": "Prof. Ricardo Souza",
                "cpf": "41628593710",
                "email": "ricardo.souza@anchieta.edu.br",
                "phone": "+5511992001001",
                "department": "Tecnologia da Informação",
                "position": "Professor Titular",
            },
            {
                "number": "FUNC002",
                "name": "Fernanda Oliveira",
                "cpf": "52739604821",
                "email": "fernanda.oliveira@anchieta.edu.br",
                "phone": "+5511992002002",
                "department": "Recursos Humanos",
                "position": "Analista de RH",
            },
            {
                "number": "FUNC003",
                "name": "Juliana Martins",
                "cpf": "63840715932",
                "email": "juliana.martins@anchieta.edu.br",
                "phone": "+5511992003003",
                "department": "Secretaria Acadêmica",
                "position": "Agente de Atendimento",
            },
        ]

        employees = []
        for e in employees_raw:
            emp = Employee(
                tenant_id=tenant_id,
                employee_number=e["number"],
                full_name=e["name"],
                cpf=e["cpf"],
                email=e["email"],
                phone=e["phone"],
                department=e["department"],
                position=e["position"],
                hire_date=date(2020, 3, 1),
                status="active",
            )
            db.add(emp)
            employees.append(emp)
        await db.flush()
        print(f"{len(employees)} funcionários criados")

        prof_ricardo, fernanda, juliana = employees

        # ══════════════════════════════════════════════════════════════════
        # HOLERITES
        # ══════════════════════════════════════════════════════════════════
        for emp in employees:
            gross = Decimal("8500.00") if emp == prof_ricardo else (
                Decimal("5200.00") if emp == fernanda else Decimal("3800.00")
            )
            for month in range(1, 4):
                net = gross * Decimal("0.72")  # ~28% descontos
                db.add(Payslip(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    reference_month=f"2026-{month:02d}",
                    gross_salary=gross,
                    net_salary=net.quantize(Decimal("0.01")),
                    deductions={
                        "INSS": float(gross * Decimal("0.14")),
                        "IRRF": float(gross * Decimal("0.10")),
                        "Vale Transporte": float(gross * Decimal("0.04")),
                    },
                ))
        await db.flush()
        print("9 holerites criados")

        # ══════════════════════════════════════════════════════════════════
        # FÉRIAS
        # ══════════════════════════════════════════════════════════════════
        for emp in employees:
            used = 10 if emp == prof_ricardo else (5 if emp == fernanda else 0)
            db.add(VacationBalance(
                tenant_id=tenant_id,
                employee_id=emp.id,
                accrual_period_start=date(2025, 3, 1),
                accrual_period_end=date(2026, 2, 28),
                total_days=30,
                used_days=used,
                deadline_date=date(2027, 2, 28),
            ))
        await db.flush()
        print("3 saldos de férias criados")

        # ══════════════════════════════════════════════════════════════════
        # REGISTROS DE PONTO (última semana)
        # ══════════════════════════════════════════════════════════════════
        for emp in employees:
            for day_offset in range(5):
                record_date = today - timedelta(days=4 - day_offset)
                if record_date.weekday() >= 5:
                    continue
                clock_in_dt = datetime(
                    record_date.year, record_date.month, record_date.day,
                    8, 0, tzinfo=timezone.utc
                )
                clock_out_dt = datetime(
                    record_date.year, record_date.month, record_date.day,
                    17, 0, tzinfo=timezone.utc
                )
                db.add(TimeRecord(
                    tenant_id=tenant_id,
                    employee_id=emp.id,
                    record_date=record_date,
                    clock_in=clock_in_dt,
                    clock_out=clock_out_dt,
                    break_start=clock_in_dt.replace(hour=12),
                    break_end=clock_in_dt.replace(hour=13),
                    total_hours=Decimal("8.0"),
                    status="regular",
                ))
        await db.flush()
        print("Registros de ponto criados")

        # ══════════════════════════════════════════════════════════════════
        # SOLICITAÇÕES RH
        # ══════════════════════════════════════════════════════════════════
        db.add(HRRequest(
            tenant_id=tenant_id,
            employee_id=prof_ricardo.id,
            request_type="vacation",
            description="Solicito 15 dias de férias a partir de 01/07/2026",
            status="approved",
            response_text="Férias aprovadas para o período 01/07 a 15/07/2026.",
        ))
        db.add(HRRequest(
            tenant_id=tenant_id,
            employee_id=fernanda.id,
            request_type="declaration",
            description="Preciso de declaração de vínculo empregatício para financiamento",
            status="pending",
        ))
        db.add(HRRequest(
            tenant_id=tenant_id,
            employee_id=juliana.id,
            request_type="medical_cert",
            description="Atestado médico de 2 dias - consulta odontológica",
            status="approved",
            response_text="Atestado aceito. Faltas abonadas nos dias 02/04 e 03/04.",
        ))
        await db.flush()
        print("3 solicitações RH criadas")

        await db.commit()

        # ══════════════════════════════════════════════════════════════════
        # RESUMO
        # ══════════════════════════════════════════════════════════════════
        print("\n" + "=" * 60)
        print("SEED PITCH DECK — DADOS PRONTOS!")
        print("=" * 60)
        print("\nALUNOS (senha = últimos 6 dígitos do CPF):")
        for s in students_raw:
            senha = s["cpf"][-6:]
            print(f"  RA: {s['ra']} | {s['name']:<30} | {s['course']:<25} | Senha: {senha} | Status: {s['status']}")

        print("\nFUNCIONÁRIOS (senha = últimos 6 dígitos do CPF):")
        for e in employees_raw:
            senha = e["cpf"][-6:]
            print(f"  {e['number']} | {e['name']:<25} | {e['department']:<25} | Senha: {senha}")

        print("\nCENÁRIOS DE DEMO:")
        print("  1. Lucas (20241001) — Eng. Software, notas boas, Cálculo III apertado")
        print("  2. Mariana (20241002) — Direito, boleto de fevereiro VENCIDO")
        print("  3. Beatriz (20241003) — Enfermagem, aluna exemplar (notas altas, 0 faltas)")
        print("  4. Rafael (20241004) — Administração, matrícula TRANCADA")
        print("  5. Camila (20241005) — Psicologia, frequência preocupante em Psicopatologia")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_pitch())
