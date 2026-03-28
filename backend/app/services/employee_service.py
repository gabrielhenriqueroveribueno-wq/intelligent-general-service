import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, HRRequest, Payslip, TimeRecord, VacationBalance
from app.utils.exceptions import NotFoundError


async def get_employee_by_number(
    db: AsyncSession, tenant_id: uuid.UUID, employee_number: str
) -> Optional[Employee]:
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.employee_number == employee_number,
        )
    )
    return result.scalar_one_or_none()


async def get_employee_by_id(
    db: AsyncSession, tenant_id: uuid.UUID, employee_id: uuid.UUID
) -> Employee:
    result = await db.execute(
        select(Employee).where(Employee.tenant_id == tenant_id, Employee.id == employee_id)
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise NotFoundError("Funcionário")
    return emp


async def list_employees(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search: Optional[str] = None,
    department: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Employee], int]:
    query = select(Employee).where(Employee.tenant_id == tenant_id)

    if search:
        query = query.where(
            Employee.full_name.ilike(f"%{search}%") | Employee.employee_number.ilike(f"%{search}%")
        )
    if department:
        query = query.where(Employee.department == department)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.offset((page - 1) * size).limit(size).order_by(Employee.full_name)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_payslips(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    reference_month: Optional[str] = None,
) -> list[Payslip]:
    query = select(Payslip).where(
        Payslip.tenant_id == tenant_id, Payslip.employee_id == employee_id
    )
    if reference_month:
        query = query.where(Payslip.reference_month == reference_month)

    result = await db.execute(query.order_by(Payslip.reference_month.desc()))
    return result.scalars().all()


async def get_vacation_balance(
    db: AsyncSession, tenant_id: uuid.UUID, employee_id: uuid.UUID
) -> Optional[VacationBalance]:
    result = await db.execute(
        select(VacationBalance)
        .where(VacationBalance.tenant_id == tenant_id, VacationBalance.employee_id == employee_id)
        .order_by(VacationBalance.accrual_period_end.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_time_records(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    month: Optional[str] = None,
) -> list[TimeRecord]:
    query = select(TimeRecord).where(
        TimeRecord.tenant_id == tenant_id, TimeRecord.employee_id == employee_id
    )
    result = await db.execute(query.order_by(TimeRecord.record_date.desc()).limit(30))
    return result.scalars().all()


async def create_hr_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    request_type: str,
    description: Optional[str],
) -> HRRequest:
    req = HRRequest(
        tenant_id=tenant_id,
        employee_id=employee_id,
        request_type=request_type,
        description=description,
        status="pending",
    )
    db.add(req)
    await db.flush()
    return req


async def get_hr_requests(
    db: AsyncSession, tenant_id: uuid.UUID, employee_id: uuid.UUID
) -> list[HRRequest]:
    result = await db.execute(
        select(HRRequest)
        .where(HRRequest.tenant_id == tenant_id, HRRequest.employee_id == employee_id)
        .order_by(HRRequest.created_at.desc())
    )
    return result.scalars().all()
