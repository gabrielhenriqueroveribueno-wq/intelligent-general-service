"""
Serviço de anonimização LGPD — Direito ao Esquecimento.

Substitui todos os dados de identificação pessoal (PII) por hashes irrecuperáveis
ou strings genéricas, mantendo a integridade referencial do banco para que
relatórios, notas e tickets continuem funcionais sem DELETE real.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _anonymous_hash(original: str) -> str:
    """Gera hash SHA-256 irreversível a partir do valor original."""
    return hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]


def _anonymous_email(original_id: str) -> str:
    """Gera e-mail fictício baseado em hash."""
    return f"anon-{_anonymous_hash(original_id)}@anonimizado.lgpd"


async def anonymize_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    reason: str = "Solicitação do titular (Art. 18, LGPD)",
    requested_by: uuid.UUID | None = None,
) -> dict:
    """Anonimiza todos os dados PII de um aluno, mantendo integridade referencial.

    Tabelas afetadas:
        - students: nome, cpf, email, phone → anonimizados
        - contacts: phone_number, name → anonimizados
        - conversations: metadata limpo
        - messages: conteúdo de mensagens do usuário → anonimizado
        - boletos: dados sensíveis → anonimizados

    Returns:
        dict com resumo da operação (tables_affected, records_updated).
    """
    from app.models.billing import Boleto
    from app.models.conversation import Contact, Conversation, Message
    from app.models.student import Student

    # ── 1. Busca o aluno ─────────────────────────────────────────────────────
    result = await db.execute(
        select(Student).where(
            Student.id == student_id,
            Student.tenant_id == tenant_id,
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise ValueError(f"Aluno {student_id} não encontrado no tenant {tenant_id}")

    if student.enrollment_status == "anonymized":
        raise ValueError(f"Aluno {student_id} já foi anonimizado anteriormente")

    anon_id = _anonymous_hash(str(student_id))
    stats: dict[str, int] = {}

    # ── 2. Anonimiza Student ─────────────────────────────────────────────────
    await db.execute(
        update(Student)
        .where(Student.id == student_id)
        .values(
            full_name=f"Aluno Anonimizado #{anon_id}",
            cpf=None,
            email=_anonymous_email(str(student_id)),
            phone=None,
            enrollment_status="anonymized",
        )
    )
    stats["students"] = 1

    # ── 3. Anonimiza Contact(s) vinculados ───────────────────────────────────
    contact_result = await db.execute(
        select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.student_id == student_id,
        )
    )
    contacts = contact_result.scalars().all()
    contact_ids = [c.id for c in contacts]

    if contact_ids:
        await db.execute(
            update(Contact)
            .where(Contact.id.in_(contact_ids))
            .values(
                phone_number=f"+00000000{anon_id[:8]}",
                name=f"Contato Anonimizado #{anon_id}",
                is_verified=False,
                metadata_=None,
            )
        )
        stats["contacts"] = len(contact_ids)

        # ── 4. Anonimiza mensagens do usuário nas conversas ──────────────────
        conv_result = await db.execute(
            select(Conversation.id).where(
                Conversation.tenant_id == tenant_id,
                Conversation.contact_id.in_(contact_ids),
            )
        )
        conv_ids = [row[0] for row in conv_result.all()]

        if conv_ids:
            # Anonimiza apenas mensagens enviadas pelo usuário (bot/agent ficam)
            msg_update = await db.execute(
                update(Message)
                .where(
                    Message.conversation_id.in_(conv_ids),
                    Message.sender_type == "user",
                )
                .values(
                    content="[Mensagem anonimizada — LGPD Art. 18]",
                    whatsapp_msg_id=None,
                    whatsapp_media_id=None,
                    media_url=None,
                )
            )
            stats["messages"] = msg_update.rowcount or 0

            # Limpa metadata das conversas
            await db.execute(
                update(Conversation)
                .where(Conversation.id.in_(conv_ids))
                .values(metadata_=None)
            )
            stats["conversations"] = len(conv_ids)

    # ── 5. Anonimiza boletos ─────────────────────────────────────────────────
    boleto_update = await db.execute(
        update(Boleto)
        .where(
            Boleto.tenant_id == tenant_id,
            Boleto.student_id == student_id,
        )
        .values(barcode=None, digitable_line=None)
    )
    stats["boletos"] = boleto_update.rowcount or 0

    # ── 6. Registra auditoria ────────────────────────────────────────────────
    from app.models.audit import AuditLog

    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=requested_by,
        action="lgpd_anonymize_student",
        entity_type="student",
        entity_id=student_id,
        details={
            "reason": reason,
            "anonymized_at": datetime.now(timezone.utc).isoformat(),
            "records_affected": stats,
        },
    )
    db.add(audit)

    await db.commit()

    logger.info(
        "Aluno %s anonimizado com sucesso: %s registros afetados",
        student_id,
        stats,
    )

    return {
        "student_id": str(student_id),
        "status": "anonymized",
        "tables_affected": list(stats.keys()),
        "records_updated": stats,
        "anonymized_at": datetime.now(timezone.utc).isoformat(),
    }


async def anonymize_employee(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID,
    reason: str = "Solicitação do titular (Art. 18, LGPD)",
    requested_by: uuid.UUID | None = None,
) -> dict:
    """Anonimiza todos os dados PII de um funcionário, mantendo integridade referencial.

    Tabelas afetadas:
        - employees: nome, cpf, email, phone → anonimizados
        - contacts: phone_number, name → anonimizados
        - conversations + messages do usuário → anonimizados
        - payslips: pdf_url removido
        - hr_requests: description e response → anonimizados

    Returns:
        dict com resumo da operação.
    """
    from app.models.conversation import Contact, Conversation, Message
    from app.models.employee import Employee, HRRequest, Payslip

    # ── 1. Busca o funcionário ───────────────────────────────────────────────
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.tenant_id == tenant_id,
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise ValueError(f"Funcionário {employee_id} não encontrado no tenant {tenant_id}")

    if employee.status == "anonymized":
        raise ValueError(f"Funcionário {employee_id} já foi anonimizado anteriormente")

    anon_id = _anonymous_hash(str(employee_id))
    stats: dict[str, int] = {}

    # ── 2. Anonimiza Employee ────────────────────────────────────────────────
    await db.execute(
        update(Employee)
        .where(Employee.id == employee_id)
        .values(
            full_name=f"Funcionário Anonimizado #{anon_id}",
            cpf=None,
            email=_anonymous_email(str(employee_id)),
            phone=None,
            status="anonymized",
        )
    )
    stats["employees"] = 1

    # ── 3. Anonimiza Contact(s) vinculados ───────────────────────────────────
    contact_result = await db.execute(
        select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.employee_id == employee_id,
        )
    )
    contacts = contact_result.scalars().all()
    contact_ids = [c.id for c in contacts]

    if contact_ids:
        await db.execute(
            update(Contact)
            .where(Contact.id.in_(contact_ids))
            .values(
                phone_number=f"+00000000{anon_id[:8]}",
                name=f"Contato Anonimizado #{anon_id}",
                is_verified=False,
                metadata_=None,
            )
        )
        stats["contacts"] = len(contact_ids)

        conv_result = await db.execute(
            select(Conversation.id).where(
                Conversation.tenant_id == tenant_id,
                Conversation.contact_id.in_(contact_ids),
            )
        )
        conv_ids = [row[0] for row in conv_result.all()]

        if conv_ids:
            msg_update = await db.execute(
                update(Message)
                .where(
                    Message.conversation_id.in_(conv_ids),
                    Message.sender_type == "user",
                )
                .values(
                    content="[Mensagem anonimizada — LGPD Art. 18]",
                    whatsapp_msg_id=None,
                    whatsapp_media_id=None,
                    media_url=None,
                )
            )
            stats["messages"] = msg_update.rowcount or 0

            await db.execute(
                update(Conversation)
                .where(Conversation.id.in_(conv_ids))
                .values(metadata_=None)
            )
            stats["conversations"] = len(conv_ids)

    # ── 4. Anonimiza payslips ────────────────────────────────────────────────
    payslip_update = await db.execute(
        update(Payslip)
        .where(
            Payslip.tenant_id == tenant_id,
            Payslip.employee_id == employee_id,
        )
        .values(pdf_url=None)
    )
    stats["payslips"] = payslip_update.rowcount or 0

    # ── 5. Anonimiza HR requests ─────────────────────────────────────────────
    hr_update = await db.execute(
        update(HRRequest)
        .where(
            HRRequest.tenant_id == tenant_id,
            HRRequest.employee_id == employee_id,
        )
        .values(
            description="[Descrição anonimizada — LGPD Art. 18]",
            response_text="[Resposta anonimizada — LGPD Art. 18]",
        )
    )
    stats["hr_requests"] = hr_update.rowcount or 0

    # ── 6. Registra auditoria ────────────────────────────────────────────────
    from app.models.audit import AuditLog

    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=requested_by,
        action="lgpd_anonymize_employee",
        entity_type="employee",
        entity_id=employee_id,
        details={
            "reason": reason,
            "anonymized_at": datetime.now(timezone.utc).isoformat(),
            "records_affected": stats,
        },
    )
    db.add(audit)

    await db.commit()

    logger.info(
        "Funcionário %s anonimizado com sucesso: %s registros afetados",
        employee_id,
        stats,
    )

    return {
        "employee_id": str(employee_id),
        "status": "anonymized",
        "tables_affected": list(stats.keys()),
        "records_updated": stats,
        "anonymized_at": datetime.now(timezone.utc).isoformat(),
    }
