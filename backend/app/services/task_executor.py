"""
Executor de tarefas reais via WhatsApp.

Executa ações no sistema baseado no intent classificado:
gerar boleto, solicitar matrícula, pedir documento, etc.
"""

import logging
import time
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Boleto
from app.models.service_request import ServiceRequest
from app.models.slide import SlidePresentation
from app.models.student import Student

logger = logging.getLogger(__name__)

# Intents que representam ações executáveis
ACTION_INTENTS = {
    "generate_boleto",
    "enrollment_request",
    "document_request",
    "class_enrollment",
    "grade_appeal",
    "transfer_request",
    "scholarship_query",
    "internship_query",
    "event_registration",
    "library_query",
    "financial_negotiation",
    "certificate_request",
    "slide_generate",
    "slide_update",
}


def is_action_intent(intent: str) -> bool:
    """Verifica se o intent é uma ação executável."""
    return intent in ACTION_INTENTS


async def execute_action(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    conversation_id: UUID | None,
    intent: str,
    entities: dict,
    student_id: UUID | None = None,
) -> dict[str, Any]:
    """
    Despacha a execução para o handler correto e registra em service_requests.
    """
    start = time.perf_counter()

    handler = _HANDLERS.get(intent, _handle_generic_request)
    result = await handler(db, tenant_id, contact_id, entities, student_id)

    elapsed = time.perf_counter() - start

    # Registra a solicitação
    sr = ServiceRequest(
        tenant_id=tenant_id,
        contact_id=contact_id,
        request_type=intent,
        status="completed" if result.get("success") else "pending",
        request_data=entities,
        result_data=result,
        conversation_id=conversation_id,
        processed_by="ai",
        processing_time_seconds=elapsed,
    )
    db.add(sr)
    await db.flush()

    return result


async def _handle_generate_boleto(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Gera um boleto para o aluno."""
    if not student_id:
        return {"success": False, "message": "Aluno não identificado para geração de boleto."}

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {"success": False, "message": "Aluno não encontrado no sistema."}

    from decimal import Decimal

    boleto = Boleto(
        tenant_id=tenant_id,
        student_id=student_id,
        reference_month=entities.get("month", "2026-03"),
        amount=Decimal(entities.get("amount", "500.00")),
        status="pending",
    )
    db.add(boleto)
    await db.flush()

    return {
        "success": True,
        "message": f"Boleto gerado com sucesso para {student.full_name}.",
        "boleto_id": str(boleto.id),
        "amount": str(boleto.amount),
        "reference_month": boleto.reference_month,
    }


async def _handle_enrollment_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra pedido de matrícula/rematrícula."""
    protocol = f"MAT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "message": (
            f"Solicitação de matrícula registrada com protocolo {protocol}. "
            "A secretaria entrará em contato em até 48h."
        ),
        "protocol": protocol,
    }


async def _handle_document_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra solicitação de documento."""
    doc_type = entities.get("type", "declaração")
    protocol = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "message": (
            f"Solicitação de {doc_type} registrada com protocolo {protocol}. "
            "Prazo de emissão: 3 a 5 dias úteis."
        ),
        "protocol": protocol,
        "document_type": doc_type,
    }


async def _handle_class_enrollment(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra inscrição em disciplina."""
    subject = entities.get("subject", "disciplina solicitada")
    protocol = f"DISC-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "message": (
            f"Inscrição na disciplina '{subject}' registrada com protocolo {protocol}. "
            "Confirmação será enviada após validação de pré-requisitos."
        ),
        "protocol": protocol,
    }


async def _handle_slide_generate(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Gera slides via IA para o professor."""
    from app.models.conversation import Contact
    from app.services.slide_service import generate_slides

    # Buscar o user (teacher) vinculado ao contato
    contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = contact_result.scalar_one_or_none()

    if not contact or not contact.employee_id:
        return {"success": False, "message": "Usuário não identificado como professor."}

    from app.models.user import User

    teacher_result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.role == "teacher").limit(1)
    )
    teacher = teacher_result.scalar_one_or_none()
    if not teacher:
        return {"success": False, "message": "Professor não encontrado no sistema."}

    subject = entities.get("subject", "Aula")
    prompt = entities.get("prompt", "Crie uma apresentação sobre o tema da aula")
    num_slides = entities.get("num_slides")

    try:
        presentation = await generate_slides(
            db=db,
            tenant_id=tenant_id,
            teacher_id=teacher.id,
            prompt=prompt,
            subject=subject,
            num_slides=int(num_slides) if num_slides else None,
        )
        await db.flush()

        return {
            "success": True,
            "message": (
                f"Apresentação '{presentation.title}' criada com sucesso! "
                f"Total de {presentation.total_slides} slides. "
                f"Acesse o painel web para visualizar e baixar."
            ),
            "presentation_id": str(presentation.id),
            "title": presentation.title,
            "total_slides": presentation.total_slides,
        }
    except Exception as e:
        logger.error("Erro ao gerar slides: %s", e)
        return {"success": False, "message": f"Erro ao gerar slides: {str(e)}"}


async def _handle_slide_update(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Atualiza slides existentes via IA."""
    from app.services.slide_service import update_slides

    presentation_id = entities.get("presentation_id")
    prompt = entities.get("prompt", "Atualize a apresentação conforme solicitado")

    if not presentation_id:
        # Busca a apresentação mais recente do tenant
        result = await db.execute(
            select(SlidePresentation)
            .where(SlidePresentation.tenant_id == tenant_id)
            .order_by(SlidePresentation.updated_at.desc())
            .limit(1)
        )
        presentation = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(SlidePresentation).where(
                SlidePresentation.id == uuid.UUID(presentation_id),
                SlidePresentation.tenant_id == tenant_id,
            )
        )
        presentation = result.scalar_one_or_none()

    if not presentation:
        return {"success": False, "message": "Nenhuma apresentação encontrada para atualizar."}

    from app.models.user import User
    teacher_result = await db.execute(
        select(User).where(User.id == presentation.teacher_id)
    )
    teacher = teacher_result.scalar_one_or_none()

    try:
        updated = await update_slides(
            db=db,
            presentation=presentation,
            prompt=prompt,
            tenant_id=tenant_id,
            teacher_id=teacher.id if teacher else presentation.teacher_id,
        )
        await db.flush()

        return {
            "success": True,
            "message": (
                f"Apresentação '{updated.title}' atualizada (v{updated.version})! "
                f"Total de {updated.total_slides} slides. "
                f"Acesse o painel para visualizar."
            ),
            "presentation_id": str(updated.id),
            "version": updated.version,
        }
    except Exception as e:
        logger.error("Erro ao atualizar slides: %s", e)
        return {"success": False, "message": f"Erro ao atualizar slides: {str(e)}"}


async def _handle_generic_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Handler genérico para demais intents de ação."""
    protocol = f"SOL-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "message": (
            f"Sua solicitação foi registrada com protocolo {protocol}. "
            "Nossa equipe analisará e retornará em breve."
        ),
        "protocol": protocol,
    }


_HANDLERS = {
    "generate_boleto": _handle_generate_boleto,
    "enrollment_request": _handle_enrollment_request,
    "document_request": _handle_document_request,
    "class_enrollment": _handle_class_enrollment,
    "grade_appeal": _handle_generic_request,
    "transfer_request": _handle_generic_request,
    "scholarship_query": _handle_generic_request,
    "internship_query": _handle_generic_request,
    "event_registration": _handle_generic_request,
    "library_query": _handle_generic_request,
    "financial_negotiation": _handle_generic_request,
    "certificate_request": _handle_generic_request,
    "slide_generate": _handle_slide_generate,
    "slide_update": _handle_slide_update,
}
