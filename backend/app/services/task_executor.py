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
    "generate_pix",
    "facility_ticket",
    "library_renewal",
    "tutor_question",
    "medical_certificate",
    "schedule_appointment",
    "cancel_appointment",
    "document_ocr",
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

    teacher_result = await db.execute(select(User).where(User.id == presentation.teacher_id))
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


async def _handle_generate_pix(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Gera link de pagamento via Mercado Pago (PIX + cartão) ou PIX BR Code."""
    if not student_id:
        return {"success": False, "message": "Aluno não identificado para geração de PIX."}

    from app.config import settings as app_settings

    # Se Mercado Pago configurado, usa Checkout Pro (PIX + cartão)
    if app_settings.MP_ACCESS_TOKEN:
        from app.services.mercadopago_service import create_checkout_for_student

        webhook_url = None
        # Em produção, configurar URL do webhook MP
        # webhook_url = "https://igs-anchieta.duckdns.org/api/v1/webhook/mercadopago"

        result = await create_checkout_for_student(
            db, tenant_id, student_id, notification_url=webhook_url
        )
        if result.get("success"):
            # Usa sandbox_url em teste, checkout_url em produção
            url = result.get("sandbox_url") or result.get("checkout_url", "")
            result["payment_url"] = url
            result["message"] = (
                f"Aqui esta o link para pagar sua mensalidade:\n\n"
                f"{url}\n\n"
                f"Valor: *R$ {result.get('amount')}*\n"
                f"Aceita *PIX*, *cartao de credito/debito* e *boleto*."
            )
        return result

    # Fallback: PIX BR Code estático
    from app.models.tenant import TenantSettings
    from app.services.payment_service import generate_pix_for_student

    ts_result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
    )
    ts = ts_result.scalar_one_or_none()
    pix_key = ""
    if ts and ts.settings:
        pix_key = ts.settings.get("pix_key", "")

    return await generate_pix_for_student(db, tenant_id, student_id, pix_key)


async def _handle_financial_negotiation(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Negocia/parcela débitos do aluno."""
    if not student_id:
        return {"success": False, "message": "Aluno não identificado para negociação."}

    from app.services.payment_service import negotiate_debt

    num_installments = int(entities.get("installments", entities.get("parcelas", 3)))
    reason = entities.get("reason", "Negociação solicitada via WhatsApp")

    return await negotiate_debt(
        db=db,
        tenant_id=tenant_id,
        student_id=student_id,
        num_installments=num_installments,
        reason=reason,
        negotiated_by="ai",
    )


async def _handle_facility_ticket(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Cria chamado de infraestrutura."""
    from app.services.ticket_service import create_ticket

    description = entities.get("description", "Chamado de infraestrutura via WhatsApp")
    location = entities.get("location", "")
    if location:
        description = f"Local: {location}\n{description}"

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject="Chamado de Infraestrutura",
        priority=entities.get("priority", "medium"),
        category="infrastructure",
        description=description,
        contact_id=contact_id,
    )

    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Chamado de infraestrutura aberto com protocolo *{ticket.protocol_number}*. "
            "Se quiser, envie uma foto do problema para anexar ao chamado. "
            "A equipe de manutenção será notificada."
        ),
    }


async def _handle_library_renewal(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Renova empréstimo de livro na biblioteca."""
    if not student_id:
        return {"success": False, "message": "Aluno não identificado."}

    from app.services.library_service import renew_active_loans

    return await renew_active_loans(db, tenant_id, student_id)


async def _handle_tutor_question(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Responde dúvida acadêmica usando material do professor."""
    if not student_id:
        return {"success": False, "message": "Aluno não identificado."}

    from app.services.tutor_service import answer_student_question

    question = entities.get("question", entities.get("prompt", ""))
    subject = entities.get("subject", "")

    return await answer_student_question(
        db=db,
        tenant_id=tenant_id,
        student_id=student_id,
        question=question,
        subject_hint=subject,
    )


async def _handle_medical_certificate(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra intenção de envio de atestado médico (processamento de imagem é feito em message_tasks)."""
    protocol = f"ATST-{uuid.uuid4().hex[:8].upper()}"
    return {
        "success": True,
        "message": (
            f"Solicitação de atestado médico registrada (protocolo *{protocol}*). "
            "Por favor, envie a *foto do atestado* nesta conversa para processamento automático."
        ),
        "protocol": protocol,
        "awaiting_image": True,
    }


async def _handle_schedule_appointment(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Agenda atendimento presencial ou mostra horários disponíveis."""
    from datetime import datetime as dt

    from app.services.appointment_service import (
        create_appointment,
        get_available_slots,
    )

    # Se já informou data e hora, cria o agendamento
    date_str = entities.get("date") or entities.get("data")
    time_str = entities.get("time") or entities.get("horario")
    department = entities.get("department", entities.get("setor", "secretaria"))

    if date_str and time_str:
        try:
            for fmt in ("%d/%m/%Y", "%d/%m", "%Y-%m-%d"):
                try:
                    parsed_date = dt.strptime(date_str, fmt).date()
                    if fmt == "%d/%m":
                        parsed_date = parsed_date.replace(year=dt.now().year)
                    break
                except ValueError:
                    continue
            else:
                return {
                    "success": False,
                    "message": "Não entendi a data. Use o formato DD/MM/AAAA.",
                }

            from datetime import time as time_type

            parts = time_str.replace("h", ":").split(":")
            parsed_time = time_type(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

            appointment = await create_appointment(
                db=db,
                tenant_id=tenant_id,
                contact_id=contact_id,
                appointment_date=parsed_date,
                appointment_time=parsed_time,
                department=department,
                reason=entities.get("reason", "Agendamento via WhatsApp"),
                student_id=student_id,
            )
            return {
                "success": True,
                "message": (
                    f"Agendamento confirmado!\n\n"
                    f"- Protocolo: *{appointment.protocol}*\n"
                    f"- Data: *{parsed_date.strftime('%d/%m/%Y')}*\n"
                    f"- Horário: *{parsed_time.strftime('%H:%M')}*\n"
                    f"- Setor: *{department.title()}*\n\n"
                    f"Apresente o protocolo na recepção."
                ),
                "protocol": appointment.protocol,
            }
        except Exception as e:
            logger.error("Erro ao criar agendamento: %s", e)
            return {"success": False, "message": "Erro ao criar o agendamento. Tente novamente."}

    # Se não informou data/hora, mostra horários disponíveis
    slots = await get_available_slots(db, tenant_id, department=department)
    available = slots.get("available_dates", {})

    if not available:
        return {
            "success": True,
            "message": "Não há horários disponíveis nos próximos dias. Tente novamente amanhã.",
            "needs_date_time": True,
        }

    lines = []
    for date_label, times in available.items():
        times_str = ", ".join(times[:6])
        if len(times) > 6:
            times_str += f" (+{len(times) - 6} horários)"
        lines.append(f"*{date_label}*: {times_str}")

    return {
        "success": True,
        "message": (
            "Horários disponíveis para atendimento:\n\n"
            + "\n".join(lines)
            + "\n\nMe diz a data e o horário que prefere."
        ),
        "needs_date_time": True,
        "available_slots": available,
    }


async def _handle_cancel_appointment(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Cancela agendamento do contato."""
    from app.services.appointment_service import cancel_appointment

    return await cancel_appointment(db, tenant_id, contact_id)


async def _handle_document_ocr(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Indica que o usuário quer enviar documento para OCR."""
    return {
        "success": True,
        "message": (
            "Pode enviar a *foto do documento* aqui que eu analiso pra você! "
            "Aceito RG, CPF, comprovante de residência, boleto, histórico escolar e outros."
        ),
        "awaiting_image": True,
    }


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
    "financial_negotiation": _handle_financial_negotiation,
    "certificate_request": _handle_generic_request,
    "slide_generate": _handle_slide_generate,
    "slide_update": _handle_slide_update,
    "generate_pix": _handle_generate_pix,
    "facility_ticket": _handle_facility_ticket,
    "library_renewal": _handle_library_renewal,
    "tutor_question": _handle_tutor_question,
    "medical_certificate": _handle_medical_certificate,
    "schedule_appointment": _handle_schedule_appointment,
    "cancel_appointment": _handle_cancel_appointment,
    "document_ocr": _handle_document_ocr,
}
