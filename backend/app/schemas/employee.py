import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    employee_number: str
    full_name: str
    department: Optional[str]
    position: Optional[str]
    status: str
    email: Optional[str]
    phone: Optional[str]

    class Config:
        from_attributes = True


class PayslipResponse(BaseModel):
    id: uuid.UUID
    reference_month: str
    gross_salary: Decimal
    net_salary: Decimal
    deductions: Optional[dict]
    pdf_url: Optional[str]

    class Config:
        from_attributes = True


class VacationBalanceResponse(BaseModel):
    id: uuid.UUID
    accrual_period_start: Optional[object]
    accrual_period_end: Optional[object]
    total_days: int
    used_days: int
    remaining_days: int
    deadline_date: Optional[object]

    class Config:
        from_attributes = True


class HRRequestCreate(BaseModel):
    request_type: str
    description: Optional[str] = None


class HRRequestResponse(BaseModel):
    id: uuid.UUID
    request_type: str
    description: Optional[str]
    status: str
    response_text: Optional[str]

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    items: List[EmployeeResponse]
    total: int
    page: int
    size: int
