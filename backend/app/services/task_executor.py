# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
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
    "generate_pix",
    "open_ticket",
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
    """Registra pedido de matrícula/rematrícula como ticket."""
    from app.services.ticket_service import create_ticket

    period = entities.get("period", entities.get("periodo", ""))
    course = entities.get("course", entities.get("curso", ""))
    description = "Solicitação de matrícula via WhatsApp."
    if course:
        description += f"\nCurso: {course}"
    if period:
        description += f"\nPeríodo: {period}"

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject="Solicitação de Matrícula/Rematrícula",
        priority="medium",
        category="enrollment",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Solicitação de matrícula registrada com protocolo *{ticket.protocol_number}*. "
            "A secretaria entrará em contato em até 48h úteis."
        ),
    }


async def _handle_document_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra solicitação de documento como ticket."""
    from app.services.ticket_service import create_ticket

    doc_type = entities.get("type", entities.get("tipo", "declaração"))
    description = f"Tipo de documento: {doc_type}\nSolicitado via WhatsApp."

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Solicitação de Documento: {doc_type.title()}",
        priority="low",
        category="document",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "document_type": doc_type,
        "message": (
            f"Solicitação de *{doc_type}* registrada com protocolo *{ticket.protocol_number}*. "
            "Prazo de emissão: 3 a 5 dias úteis."
        ),
    }


async def _handle_class_enrollment(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra inscrição em disciplina como ticket."""
    from app.services.ticket_service import create_ticket

    subject_name = entities.get("subject", entities.get("disciplina", "disciplina solicitada"))
    description = f"Disciplina: {subject_name}\nSolicitado via WhatsApp."

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Inscrição em Disciplina: {subject_name}",
        priority="medium",
        category="academic",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Inscrição na disciplina *{subject_name}* registrada com protocolo *{ticket.protocol_number}*. "
            "Confirmação será enviada após validação de pré-requisitos."
        ),
    }


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


async def _handle_open_ticket(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Cria chamado de suporte geral para qualquer problema não categorizado."""
    from app.services.ticket_service import create_ticket

    subject = entities.get("subject", "Chamado de Suporte via WhatsApp")
    description = entities.get("description", "Chamado aberto via WhatsApp")
    priority = entities.get("priority", "medium")

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=subject,
        priority=priority,
        category="support",
        description=description,
        contact_id=contact_id,
    )

    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Chamado aberto com protocolo *{ticket.protocol_number}*. "
            "Nossa equipe entrará em contato em breve. "
            "Você pode acompanhar pelo painel ou aguardar nossa resposta aqui."
        ),
    }


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


async def _handle_grade_appeal(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Abre ticket de recurso de nota."""
    from app.services.ticket_service import create_ticket

    discipline = entities.get("discipline", entities.get("disciplina", ""))
    grade = entities.get("grade", entities.get("nota", ""))
    reason = entities.get("reason", entities.get("motivo", "Recurso solicitado via WhatsApp"))

    description = reason
    if discipline:
        description = f"Disciplina: {discipline}\n" + description
    if grade:
        description += f"\nNota contestada: {grade}"

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Recurso de Nota{f' – {discipline}' if discipline else ''}",
        priority="medium",
        category="academic",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Recurso de nota registrado com protocolo *{ticket.protocol_number}*. "
            "A coordenação acadêmica analisará em até 5 dias úteis."
        ),
    }


async def _handle_transfer_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Abre ticket de pedido de transferência."""
    from app.services.ticket_service import create_ticket

    destination = entities.get("destination", entities.get("destino", ""))
    reason = entities.get("reason", entities.get("motivo", "Transferência solicitada via WhatsApp"))
    description = reason
    if destination:
        description = f"Destino: {destination}\n" + description

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject="Solicitação de Transferência",
        priority="medium",
        category="enrollment",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Pedido de transferência registrado com protocolo *{ticket.protocol_number}*. "
            "A secretaria entrará em contato com os próximos passos em até 3 dias úteis."
        ),
    }


async def _handle_scholarship_query(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Abre ticket sobre bolsas de estudo."""
    from app.services.ticket_service import create_ticket

    scholarship_type = entities.get("type", entities.get("tipo", "bolsa"))
    description = (
        f"Tipo de bolsa: {scholarship_type}\n"
        "Consulta sobre bolsa solicitada via WhatsApp."
    )

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Consulta de Bolsa: {scholarship_type.title()}",
        priority="medium",
        category="financial",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Sua consulta sobre *{scholarship_type}* foi registrada com protocolo *{ticket.protocol_number}*. "
            "O setor financeiro entrará em contato com as opções disponíveis."
        ),
    }


async def _handle_internship_query(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Abre ticket sobre estágio."""
    from app.services.ticket_service import create_ticket

    area = entities.get("area", "")
    description = "Consulta sobre estágio via WhatsApp."
    if area:
        description = f"Área de interesse: {area}\n" + description

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Consulta de Estágio{f' – {area}' if area else ''}",
        priority="low",
        category="academic",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Consulta de estágio registrada com protocolo *{ticket.protocol_number}*. "
            "O setor de estágios entrará em contato com as oportunidades disponíveis."
        ),
    }


async def _handle_event_registration(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Registra inscrição em evento."""
    from app.services.ticket_service import create_ticket

    event_name = entities.get("event", entities.get("evento", "evento solicitado"))
    date = entities.get("date", entities.get("data", ""))
    description = f"Evento: {event_name}"
    if date:
        description += f"\nData: {date}"

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Inscrição em Evento: {event_name}",
        priority="low",
        category="event",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Inscrição no evento *{event_name}* registrada com protocolo *{ticket.protocol_number}*. "
            "Você receberá a confirmação e mais detalhes em breve."
        ),
    }


async def _handle_library_query(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Consulta disponibilidade de livro na biblioteca."""
    from app.services.library_service import search_books

    title = entities.get("title", entities.get("titulo", entities.get("book", "")))
    author = entities.get("author", entities.get("autor", ""))
    query = title or author

    if query:
        books = await search_books(db, tenant_id, query=query)
        if books:
            lines = []
            for b in books[:5]:
                status = "Disponível" if b.available_copies > 0 else "Emprestado"
                lines.append(f"• *{b.title}* — {b.author} [{status}]")
            return {
                "success": True,
                "message": (
                    f"Encontrei {len(books)} resultado(s) na biblioteca:\n\n"
                    + "\n".join(lines)
                    + ("\n\n_Mostrando os 5 primeiros._" if len(books) > 5 else "")
                    + "\n\nPara reservar ou renovar, fale com a biblioteca."
                ),
                "count": len(books),
            }
        return {
            "success": True,
            "message": (
                f"Não encontrei *{query}* no acervo. "
                "Tente outro título ou autor, ou fale com a biblioteca."
            ),
        }

    return {
        "success": True,
        "message": "Qual livro você está procurando? Me diga o título ou o nome do autor.",
        "needs_input": True,
    }


async def _handle_certificate_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Solicita certificado ou diploma."""
    from app.services.ticket_service import create_ticket

    cert_type = entities.get("type", entities.get("tipo", "certificado"))
    purpose = entities.get("purpose", entities.get("finalidade", ""))
    description = f"Tipo: {cert_type}"
    if purpose:
        description += f"\nFinalidade: {purpose}"

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject=f"Solicitação de {cert_type.title()}",
        priority="medium",
        category="document",
        description=description,
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Solicitação de *{cert_type}* registrada com protocolo *{ticket.protocol_number}*. "
            "Prazo de emissão: 5 a 10 dias úteis. "
            "Você será notificado quando estiver disponível para retirada."
        ),
    }


async def _handle_generic_request(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    entities: dict,
    student_id: UUID | None,
) -> dict[str, Any]:
    """Handler genérico para demais intents de ação."""
    from app.services.ticket_service import create_ticket

    ticket = await create_ticket(
        db=db,
        tenant_id=tenant_id,
        subject="Solicitação via WhatsApp",
        priority="medium",
        category="support",
        description="Solicitação genérica registrada via WhatsApp.",
        contact_id=contact_id,
    )
    return {
        "success": True,
        "ticket_id": str(ticket.id),
        "protocol": ticket.protocol_number,
        "message": (
            f"Sua solicitação foi registrada com protocolo *{ticket.protocol_number}*. "
            "Nossa equipe analisará e retornará em breve."
        ),
    }


_HANDLERS = {
    "generate_boleto": _handle_generate_boleto,
    "enrollment_request": _handle_enrollment_request,
    "document_request": _handle_document_request,
    "class_enrollment": _handle_class_enrollment,
    "grade_appeal": _handle_grade_appeal,
    "transfer_request": _handle_transfer_request,
    "scholarship_query": _handle_scholarship_query,
    "internship_query": _handle_internship_query,
    "event_registration": _handle_event_registration,
    "library_query": _handle_library_query,
    "financial_negotiation": _handle_financial_negotiation,
    "certificate_request": _handle_certificate_request,
    "generate_pix": _handle_generate_pix,
    "open_ticket": _handle_open_ticket,
    "facility_ticket": _handle_facility_ticket,
    "library_renewal": _handle_library_renewal,
    "tutor_question": _handle_tutor_question,
    "medical_certificate": _handle_medical_certificate,
    "schedule_appointment": _handle_schedule_appointment,
    "cancel_appointment": _handle_cancel_appointment,
    "document_ocr": _handle_document_ocr,
}
