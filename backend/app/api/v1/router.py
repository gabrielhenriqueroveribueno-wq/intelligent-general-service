from fastapi import APIRouter

from app.api.v1 import (
    auth,
    tenants,
    users,
    students,
    employees,
    conversations,
    tickets,
    knowledge_base,
    dashboard,
    reports,
    webhook,
    health,
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
