from app.models.audit import AuditLog, SLAConfig
from app.models.base import Base
from app.models.billing import Boleto
from app.models.conversation import Contact, Conversation, Message
from app.models.employee import Employee, HRRequest, Payslip, TimeRecord, VacationBalance
from app.models.knowledge_base import KBArticle, KBCategory
from app.models.schedule import ClassSchedule
from app.models.student import AttendanceRecord, Grade, Student
from app.models.tenant import Tenant, TenantSettings
from app.models.ticket import Ticket, TicketComment
from app.models.user import User

__all__ = [
    "Base",
    "Tenant", "TenantSettings",
    "User",
    "Student", "Grade", "AttendanceRecord",
    "Employee", "Payslip", "VacationBalance", "TimeRecord", "HRRequest",
    "Contact", "Conversation", "Message",
    "Ticket", "TicketComment",
    "KBCategory", "KBArticle",
    "Boleto",
    "ClassSchedule",
    "AuditLog", "SLAConfig",
]
