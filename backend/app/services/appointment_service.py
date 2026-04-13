"""
Servico de agendamento de atendimento presencial via WhatsApp.
Permite que alunos/funcionários agendem visita à secretaria, coordenação etc.
"""

import logging
import uuid
from datetime import date, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment

logger = logging.getLogger(__name__)

# Horários disponíveis para agendamento (segunda a sexta)
AVAILABLE_HOURS = [
    time(8, 0),
    time(8, 30),
    time(9, 0),
    time(9, 30),
    time(10, 0),
    time(10, 30),
    time(11, 0),
    time(11, 30),
    time(13, 0),
    time(13, 30),
    time(14, 0),
    time(14, 30),
    time(15, 0),
    time(15, 30),
    time(16, 0),
    time(16, 30),
]

DEPARTMENTS = {
    "secretaria": "Secretaria Acadêmica",
    "coordenacao": "Coordenação de Curso",
    "financeiro": "Setor Financeiro",
    "biblioteca": "Biblioteca",
    "ti": "Suporte de TI",
}

MAX_APPOINTMENTS_PER_SLOT = 3


async def get_available_slots(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    target_date: date | None = None,
    department: str = "secretaria",
) -> dict:
    """
    Retorna horários disponíveis para agendamento.
    Se target_date não informada, retorna próximos 3 dias úteis.
    """
    if target_date is None:
        dates = _next_business_days(3)
    else:
        dates = [target_date] if target_date.weekday() < 5 else []

    if not dates:
        return {"available_dates": [], "message": "Nenhum dia útil disponível."}

    result = await db.execute(
        select(Appointment.appointment_date, Appointment.appointment_time, func.count())
        .where(
            Appointment.tenant_id == tenant_id,
            Appointment.department == department,
            Appointment.appointment_date.in_(dates),
            Appointment.status.in_(["scheduled", "confirmed"]),
        )
        .group_by(Appointment.appointment_date, Appointment.appointment_time)
    )
    booked = {(row[0], row[1]): row[2] for row in result.all()}

    available = {}
    for d in dates:
        slots = []
        for h in AVAILABLE_HOURS:
            count = booked.get((d, h), 0)
            if count < MAX_APPOINTMENTS_PER_SLOT:
                slots.append(h.strftime("%H:%M"))
        if slots:
            available[d.strftime("%d/%m/%Y")] = slots

    return {"available_dates": available}


async def create_appointment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    appointment_date: date,
    appointment_time: time,
    department: str = "secretaria",
    reason: str | None = None,
    student_id: uuid.UUID | None = None,
    employee_id: uuid.UUID | None = None,
) -> Appointment:
    """Cria um agendamento."""
    protocol = f"AGD-{uuid.uuid4().hex[:8].upper()}"

    appointment = Appointment(
        tenant_id=tenant_id,
        contact_id=contact_id,
        student_id=student_id,
        employee_id=employee_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        department=department,
        reason=reason,
        status="scheduled",
        protocol=protocol,
    )
    db.add(appointment)
    await db.flush()

    logger.info(
        "Agendamento criado: %s em %s %s (%s)",
        protocol,
        appointment_date,
        appointment_time,
        department,
    )
    return appointment


async def cancel_appointment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> dict:
    """Cancela o agendamento mais recente do contato."""
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.tenant_id == tenant_id,
            Appointment.contact_id == contact_id,
            Appointment.status.in_(["scheduled", "confirmed"]),
        )
        .order_by(Appointment.appointment_date.desc())
        .limit(1)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        return {"success": False, "message": "Nenhum agendamento ativo encontrado."}

    appointment.status = "cancelled"
    await db.flush()

    return {
        "success": True,
        "message": (
            f"Agendamento *{appointment.protocol}* cancelado. "
            f"Era para *{appointment.appointment_date.strftime('%d/%m/%Y')}* "
            f"às *{appointment.appointment_time.strftime('%H:%M')}*."
        ),
        "protocol": appointment.protocol,
    }


async def get_contact_appointments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> list[dict]:
    """Retorna agendamentos ativos do contato."""
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.tenant_id == tenant_id,
            Appointment.contact_id == contact_id,
            Appointment.status.in_(["scheduled", "confirmed"]),
            Appointment.appointment_date >= date.today(),
        )
        .order_by(Appointment.appointment_date, Appointment.appointment_time)
    )
    appointments = result.scalars().all()

    return [
        {
            "protocol": a.protocol,
            "date": a.appointment_date.strftime("%d/%m/%Y"),
            "time": a.appointment_time.strftime("%H:%M"),
            "department": DEPARTMENTS.get(a.department, a.department),
            "status": a.status,
        }
        for a in appointments
    ]


def _next_business_days(n: int) -> list[date]:
    """Retorna os próximos N dias úteis a partir de amanhã."""
    days = []
    current = date.today() + timedelta(days=1)
    while len(days) < n:
        if current.weekday() < 5:  # segunda a sexta
            days.append(current)
        current += timedelta(days=1)
    return days
