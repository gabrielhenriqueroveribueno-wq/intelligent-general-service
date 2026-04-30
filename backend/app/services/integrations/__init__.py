"""
Pacote de integracoes com sistemas academicos externos.

Cada integracao implementa o Protocol AcademicSystemIntegrator e eh
registrada em registry.py para ser instanciada por tipo.
"""

from app.services.integrations.base import (
    AcademicSystemIntegrator,
    SyncResult,
)
from app.services.integrations.registry import get_integrator

__all__ = [
    "AcademicSystemIntegrator",
    "SyncResult",
    "get_integrator",
]
