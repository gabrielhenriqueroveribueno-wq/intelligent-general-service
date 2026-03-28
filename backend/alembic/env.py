import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Importa todos os models para que o Alembic os detecte
from app.models.base import Base  # noqa: F401
from app.models.tenant import Tenant, TenantSettings  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.student import Student, Grade, AttendanceRecord  # noqa: F401
from app.models.employee import Employee, Payslip, VacationBalance, TimeRecord, HRRequest  # noqa: F401
from app.models.conversation import Contact, Conversation, Message  # noqa: F401
from app.models.ticket import Ticket, TicketComment  # noqa: F401
from app.models.knowledge_base import KBCategory, KBArticle  # noqa: F401
from app.models.billing import Boleto  # noqa: F401
from app.models.schedule import ClassSchedule  # noqa: F401
from app.models.audit import AuditLog, SLAConfig  # noqa: F401
from app.models.metrics import ResponseTimeMetric, WhatsAppMonitoredAccount  # noqa: F401
from app.models.notification import MessageTemplate, ScheduledNotification  # noqa: F401
from app.models.satisfaction import OnboardingSession, SatisfactionSurvey  # noqa: F401
from app.models.service_request import ServiceRequest  # noqa: F401
from app.models.ticket_learning import TicketResolution  # noqa: F401
from app.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Sobrescreve a URL do banco com a variável de ambiente
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
