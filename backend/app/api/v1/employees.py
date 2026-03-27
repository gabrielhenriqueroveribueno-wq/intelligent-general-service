import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_tenant_id, require_roles
from app.schemas.employee import (
    EmployeeListResponse,
    EmployeeResponse,
    HRRequestCreate,
    HRRequestResponse,
    PayslipResponse,
    VacationBalanceResponse,
)
from app.services import employee_service

router = APIRouter()


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    search: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    employees, total = await employee_service.list_employees(
        db, tenant_id, search, department, page, size
    )
    return EmployeeListResponse(
        items=[EmployeeResponse.model_validate(e) for e in employees],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    employee = await employee_service.get_employee_by_id(db, tenant_id, employee_id)
    return EmployeeResponse.model_validate(employee)


@router.get("/{employee_id}/payslips", response_model=list[PayslipResponse])
async def get_payslips(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
    month: Optional[str] = Query(default=None),
):
    payslips = await employee_service.get_payslips(db, tenant_id, employee_id, month)
    return [PayslipResponse.model_validate(p) for p in payslips]


@router.get("/{employee_id}/vacation", response_model=Optional[VacationBalanceResponse])
async def get_vacation(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    vacation = await employee_service.get_vacation_balance(db, tenant_id, employee_id)
    if vacation:
        return VacationBalanceResponse.model_validate(vacation)
    return None


@router.get("/{employee_id}/requests", response_model=list[HRRequestResponse])
async def get_hr_requests(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    requests = await employee_service.get_hr_requests(db, tenant_id, employee_id)
    return [HRRequestResponse.model_validate(r) for r in requests]


@router.post("/{employee_id}/requests", response_model=HRRequestResponse, status_code=201)
async def create_hr_request(
    employee_id: uuid.UUID,
    body: HRRequestCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(require_roles("super_admin", "admin", "manager", "agent")),
):
    req = await employee_service.create_hr_request(
        db, tenant_id, employee_id, body.request_type, body.description
    )
    return HRRequestResponse.model_validate(req)


@router.patch("/{employee_id}/requests/{request_id}", response_model=HRRequestResponse)
async def respond_hr_request(
    employee_id: uuid.UUID,
    request_id: uuid.UUID,
    response_text: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user=Depends(require_roles("super_admin", "admin", "manager")),
):
    from sqlalchemy import select, update

    from app.models.employee import HRRequest

    await db.execute(
        update(HRRequest)
        .where(HRRequest.id == request_id, HRRequest.employee_id == employee_id)
        .values(
            status=status,
            response_text=response_text,
            responded_by=current_user.id,
            responded_at=datetime.now(timezone.utc),
        )
    )
    result = await db.execute(select(HRRequest).where(HRRequest.id == request_id))
    return HRRequestResponse.model_validate(result.scalar_one())
