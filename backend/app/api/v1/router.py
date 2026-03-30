from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    conversations,
    dashboard,
    employees,
    health,
    knowledge_base,
    metrics,
    reports,
    slides,
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
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(webhooks_config.router, prefix="/webhooks", tags=["Webhooks Config"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(slides.router, prefix="/slides", tags=["Slides"])
