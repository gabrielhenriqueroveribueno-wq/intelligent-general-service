"""Enable Row-Level Security on all tenant-scoped tables.

Creates RLS policies that filter rows by current_setting('app.current_tenant').
The app user (igs_user) sees only rows matching their tenant_id.
The postgres superuser and roles with BYPASSRLS bypass RLS automatically.

Revision ID: b7e2a9f3c1d8
Revises: a3f1b2c4d5e6
Create Date: 2026-04-01
"""

from alembic import op

revision = "b7e2a9f3c1d8"
down_revision = "a3f1b2c4d5e6"
branch_labels = None
depends_on = None

# All tables that have tenant_id column (from TenantMixin)
RLS_TABLES = [
    "students",
    "grades",
    "attendance_records",
    "employees",
    "payslips",
    "vacation_balances",
    "time_records",
    "hr_requests",
    "boletos",
    "contacts",
    "conversations",
    "messages",
    "tickets",
    "ticket_comments",
    "kb_categories",
    "kb_articles",
    "slide_templates",
    "slide_presentations",
    "slide_generation_logs",
    "class_schedules",
    "message_templates",
    "scheduled_notifications",
    "satisfaction_surveys",
    "onboarding_sessions",
    "service_requests",
    "response_time_metrics",
    "whatsapp_monitored_accounts",
    "ticket_resolutions",
    "audit_logs",
    "sla_configs",
    "webhook_endpoints",
    "webhook_deliveries",
    "tenant_settings",
]


def upgrade() -> None:
    # ── 1. Create dedicated app role (non-superuser) ──────────────────────
    # This role is used by the FastAPI/Celery app. It does NOT bypass RLS.
    # The migration runs as the DB owner (superuser), so it can create roles.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'igs_app') THEN
                CREATE ROLE igs_app LOGIN PASSWORD 'igs_app_secure_2026'
                    NOSUPERUSER NOCREATEDB NOCREATEROLE;
            END IF;
        END
        $$;
        """
    )

    # Grant necessary permissions to igs_app
    op.execute("GRANT CONNECT ON DATABASE igs_db TO igs_app;")
    op.execute("GRANT USAGE ON SCHEMA public TO igs_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO igs_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO igs_app;")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO igs_app;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO igs_app;"
    )

    # ── 2. Enable RLS + create policies on each tenant-scoped table ───────
    for table in RLS_TABLES:
        # Enable RLS on the table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Force RLS even for table owner (igs_user superuser still bypasses)
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Policy: SELECT — app can only read rows matching session tenant
        op.execute(
            f"""
            CREATE POLICY rls_{table}_select ON {table}
                FOR SELECT
                TO igs_app
                USING (
                    tenant_id::text = current_setting('app.current_tenant', true)
                );
            """
        )

        # Policy: INSERT — app can only insert rows for current tenant
        op.execute(
            f"""
            CREATE POLICY rls_{table}_insert ON {table}
                FOR INSERT
                TO igs_app
                WITH CHECK (
                    tenant_id::text = current_setting('app.current_tenant', true)
                );
            """
        )

        # Policy: UPDATE — app can only update rows of current tenant
        op.execute(
            f"""
            CREATE POLICY rls_{table}_update ON {table}
                FOR UPDATE
                TO igs_app
                USING (
                    tenant_id::text = current_setting('app.current_tenant', true)
                )
                WITH CHECK (
                    tenant_id::text = current_setting('app.current_tenant', true)
                );
            """
        )

        # Policy: DELETE — app can only delete rows of current tenant
        op.execute(
            f"""
            CREATE POLICY rls_{table}_delete ON {table}
                FOR DELETE
                TO igs_app
                USING (
                    tenant_id::text = current_setting('app.current_tenant', true)
                );
            """
        )

    # ── 3. Celery global-access policy ────────────────────────────────────
    # For batch tasks that need cross-tenant access (SLA check, notifications),
    # create a separate role with BYPASSRLS.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'igs_worker') THEN
                CREATE ROLE igs_worker LOGIN PASSWORD 'igs_worker_secure_2026'
                    NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS;
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT CONNECT ON DATABASE igs_db TO igs_worker;")
    op.execute("GRANT USAGE ON SCHEMA public TO igs_worker;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO igs_worker;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO igs_worker;")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO igs_worker;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO igs_worker;"
    )

    # ── 4. Tables NOT scoped by tenant (users, tenants) ───────────────────
    # These tables do NOT get RLS because:
    # - "tenants" is the root tenant table itself
    # - "users" has tenant_id but auth queries need cross-tenant access
    # - "failed_tasks" is operational DLQ
    # Instead, access is controlled at the application layer.


def downgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS rls_{table}_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS rls_{table}_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS rls_{table}_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS rls_{table}_delete ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP ROLE IF EXISTS igs_app;")
    op.execute("DROP ROLE IF EXISTS igs_worker;")
