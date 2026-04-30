from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai_health,
    auth,
    billing,
    conversations,
    dashboard,
    employees,
    evasion,
    health,
    integrations,
    knowledge_base,
    metrics,
    onboarding,
    push_subscriptions,
    report_subscriptions,
    reports,
    slides,
    student_portal,
    students,
    templates,
    tenants,
    tickets,
    users,
    webhook,
    webhooks_config,
    ws,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(knowledge_base.router, prefix="/kb", tags=["Knowledge Base"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
api_router.include_router(ws.router, tags=["WebSocket"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(ai_health.router, prefix="/admin", tags=["AI Health"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(
    report_subscriptions.router,
    prefix="/report-subscriptions",
    tags=["Report Subscriptions"],
)
api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["Academic Integrations"],
)
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(webhooks_config.router, prefix="/webhooks", tags=["Webhooks Config"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(slides.router, prefix="/slides", tags=["Slides"])
api_router.include_router(student_portal.router, prefix="/portal/student", tags=["Student Portal"])
api_router.include_router(push_subscriptions.router, tags=["Push Notifications"])
api_router.include_router(evasion.router, tags=["Evasion"])
api_router.include_router(billing.router, prefix="/billing", tags=["SaaS Billing"])
