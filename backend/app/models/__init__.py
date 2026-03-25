from app.models.base import Base
from app.models.tenant import Tenant, TenantSettings
from app.models.user import User
from app.models.student import Student, Grade, AttendanceRecord
from app.models.employee import Employee, Payslip, VacationBalance, TimeRecord, HRRequest
from app.models.conversation import Contact, Conversation, Message
from app.models.ticket import Ticket, TicketComment
from app.models.knowledge_base import KBCategory, KBArticle
from app.models.billing import Boleto
from app.models.schedule import ClassSchedule
from app.models.audit import AuditLog, SLAConfig

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
