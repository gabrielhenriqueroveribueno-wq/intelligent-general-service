import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class StudentResponse(BaseModel):
    id: uuid.UUID
    registration_number: str
    full_name: str
    course: Optional[str]
    semester: Optional[int]
    enrollment_status: str
    email: Optional[str]
    phone: Optional[str]

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    id: uuid.UUID
    subject_name: str
    subject_code: Optional[str]
    academic_period: str
    grade_value: Optional[Decimal]
    grade_type: str
    status: Optional[str]

    class Config:
        from_attributes = True


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    subject_name: Optional[str]
    subject_code: Optional[str]
    academic_period: str
    total_classes: int
    attended: int
    absence_pct: Optional[Decimal]

    class Config:
        from_attributes = True


class BoletoResponse(BaseModel):
    id: uuid.UUID
    reference_month: str
    amount: Decimal
    due_date: Optional[object]
    status: str
    barcode: Optional[str]
    pdf_url: Optional[str]

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    size: int
