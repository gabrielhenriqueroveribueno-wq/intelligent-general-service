from app.models.audit import AuditLog, FailedTask, SLAConfig
from app.models.base import Base
from app.models.billing import Boleto
from app.models.conversation import Contact, Conversation, Message
from app.models.employee import Employee, HRRequest, Payslip, TimeRecord, VacationBalance
from app.models.knowledge_base import KBArticle, KBCategory
from app.models.metrics import ResponseTimeMetric, WhatsAppMonitoredAccount
from app.models.notification import MessageTemplate, ScheduledNotification
from app.models.satisfaction import OnboardingSession, SatisfactionSurvey
from app.models.schedule import ClassSchedule
from app.models.service_request import ServiceRequest
from app.models.student import AttendanceRecord, Grade, Student
from app.models.tenant import Tenant, TenantSettings
from app.models.ticket import Ticket, TicketComment
from app.models.ticket_learning import TicketResolution
from app.models.user import User

__all__ = [
    "Base",
    "Tenant",
    "TenantSettings",
    "User",
    "Student",
    "Grade",
    "AttendanceRecord",
    "Employee",
    "Payslip",
    "VacationBalance",
    "TimeRecord",
    "HRRequest",
    "Contact",
    "Conversation",
    "Message",
    "Ticket",
    "TicketComment",
    "KBCategory",
    "KBArticle",
    "Boleto",
    "ClassSchedule",
    "AuditLog",
    "FailedTask",
    "SLAConfig",
    "MessageTemplate",
    "ScheduledNotification",
    "TicketResolution",
    "ResponseTimeMetric",
    "WhatsAppMonitoredAccount",
    "ServiceRequest",
    "SatisfactionSurvey",
    "OnboardingSession",
]
