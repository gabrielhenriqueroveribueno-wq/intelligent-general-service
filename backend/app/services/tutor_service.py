# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Serviço de Tutor Pedagógico — RAG acadêmico.

Fluxo:
1. Aluno envia dúvida via WhatsApp
2. Sistema identifica disciplinas do aluno (via ClassSchedule)
3. Busca ClassMaterial correspondente (texto extraído do PDF)
4. Envia dúvida + contexto do material para IA
5. IA explica usando exclusivamente o conteúdo do professor
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import ClassMaterial
from app.models.schedule import ClassSchedule
from app.models.student import Student
from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)

TUTOR_SYSTEM_PROMPT = """Você é um tutor pedagógico de uma instituição de ensino.
Sua função é ajudar o aluno a entender o conteúdo da disciplina.

REGRAS OBRIGATÓRIAS:
1. Responda APENAS com base no material fornecido abaixo (contexto do professor).
2. Se o material não contiver informação suficiente, diga: "Não encontrei essa informação no material disponível. Consulte seu professor."
3. Use linguagem acessível e exemplos práticos.
4. Formate a resposta de forma clara (tópicos, numeração).
5. NÃO invente dados, fórmulas ou conceitos que não estejam no material.
6. Responda em português brasileiro.

Material da disciplina:
{material_context}

Disciplina: {subject_name}
"""


async def _get_student_subjects(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
) -> list[dict]:
    """Retorna as disciplinas atuais do aluno via ClassSchedule."""
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    schedules = await db.execute(
        select(ClassSchedule).where(
            ClassSchedule.tenant_id == tenant_id,
            ClassSchedule.course == student.course,
            ClassSchedule.semester == student.semester,
        )
    )
    subjects_seen = set()
    subjects = []
    for s in schedules.scalars().all():
        key = s.subject_code or s.subject_name
        if key not in subjects_seen:
            subjects_seen.add(key)
            subjects.append(
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                }
            )
    return subjects


async def _find_relevant_materials(
    db: AsyncSession,
    tenant_id: UUID,
    subject_code: Optional[str],
    subject_name: Optional[str],
    query: str,
    limit: int = 3,
) -> list[ClassMaterial]:
    """Busca materiais relevantes para a dúvida do aluno."""
    stmt = select(ClassMaterial).where(
        ClassMaterial.tenant_id == tenant_id,
        ClassMaterial.is_active.is_(True),
        ClassMaterial.extracted_text.isnot(None),
    )

    # Filter by subject if known
    if subject_code:
        stmt = stmt.where(ClassMaterial.subject_code == subject_code)
    elif subject_name:
        stmt = stmt.where(ClassMaterial.subject_name.ilike(f"%{subject_name}%"))

    # Text search in extracted content
    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            (ClassMaterial.extracted_text.ilike(search_pattern))
            | (ClassMaterial.title.ilike(search_pattern))
            | (ClassMaterial.description.ilike(search_pattern))
        )

    stmt = stmt.order_by(ClassMaterial.upload_date.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _find_materials_by_student_subjects(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
    query: str,
    limit: int = 3,
) -> tuple[list[ClassMaterial], str]:
    """Busca materiais nas disciplinas do aluno."""
    subjects = await _get_student_subjects(db, tenant_id, student_id)
    if not subjects:
        return [], ""

    all_materials = []
    subject_name = ""

    for subj in subjects:
        materials = await _find_relevant_materials(
            db=db,
            tenant_id=tenant_id,
            subject_code=subj["subject_code"],
            subject_name=subj["subject_name"],
            query=query,
            limit=limit,
        )
        if materials:
            all_materials.extend(materials)
            if not subject_name:
                subject_name = subj["subject_name"]

    return all_materials[:limit], subject_name


async def answer_student_question(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
    question: str,
    subject_hint: str = "",
) -> dict:
    """
    Responde uma dúvida acadêmica do aluno usando material do professor (RAG).

    Args:
        question: A dúvida do aluno
        subject_hint: Nome ou código da disciplina (se extraído das entities)

    Returns:
        dict com resposta e metadados.
    """
    if not question:
        return {"success": False, "message": "Por favor, descreva sua dúvida."}

    # 1. Find relevant materials
    if subject_hint:
        materials = await _find_relevant_materials(
            db=db,
            tenant_id=tenant_id,
            subject_code=None,
            subject_name=subject_hint,
            query=question,
        )
        subject_name = subject_hint
    else:
        materials, subject_name = await _find_materials_by_student_subjects(
            db=db,
            tenant_id=tenant_id,
            student_id=student_id,
            query=question,
        )

    if not materials:
        return {
            "success": True,
            "message": (
                "Não encontrei material de aula relacionado à sua dúvida. "
                "Tente especificar a disciplina ou consulte seu professor diretamente."
            ),
            "source": "no_material",
        }

    # 2. Build material context (truncate to avoid token overflow)
    material_chunks = []
    total_chars = 0
    max_chars = 6000  # ~1500 tokens

    for mat in materials:
        text = mat.extracted_text or ""
        if total_chars + len(text) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 200:
                text = text[:remaining] + "..."
            else:
                break

        material_chunks.append(f"--- Material: {mat.title} ---\n{text}")
        total_chars += len(text)

    material_context = "\n\n".join(material_chunks)
    effective_subject = subject_name or materials[0].subject_name

    # 3. Generate answer via AI
    system_prompt = TUTOR_SYSTEM_PROMPT.format(
        material_context=material_context,
        subject_name=effective_subject,
    )

    try:
        response = await ai_complete(
            system=system_prompt,
            message=question,
            max_tokens=800,
        )

        return {
            "success": True,
            "message": response.text,
            "subject": effective_subject,
            "materials_used": [mat.title for mat in materials],
            "tokens_used": response.tokens_used,
            "source": "tutor_rag",
        }
    except Exception as e:
        logger.error("Erro no tutor pedagógico: %s", e)
        return {
            "success": False,
            "message": "Desculpe, não consegui processar sua dúvida no momento. Tente novamente.",
        }
