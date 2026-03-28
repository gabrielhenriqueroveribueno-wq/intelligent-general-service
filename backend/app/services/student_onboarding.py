"""
Serviço de autocadastro de aluno via WhatsApp.

Fluxo step-by-step:
1. welcome -> pergunta tipo (aluno, funcionário, inscrição)
2. name -> coleta nome completo
3. cpf -> coleta e valida CPF
4. email -> coleta email
5. course -> coleta curso desejado
6. confirm -> confirmação e criação do registro
"""

import logging
import re
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.satisfaction import OnboardingSession
from app.models.student import Student

logger = logging.getLogger(__name__)

STEPS = {
    "welcome": (
        "Bem-vindo! Para iniciar seu cadastro, vou precisar de algumas informações.\n"
        "Qual é o seu *nome completo*?"
    ),
    "name": "Obrigado, {name}! Agora informe seu *CPF* (apenas números):",
    "cpf": "Perfeito! Qual é o seu *e-mail*?",
    "email": (
        "Agora me diga: qual *curso* você deseja?\n"
        "Ex: Engenharia de Software, Administração, Direito..."
    ),
    "course": (
        "Confirme seus dados:\n"
        "- Nome: {name}\n"
        "- CPF: {cpf}\n"
        "- E-mail: {email}\n"
        "- Curso: {course}\n\n"
        'Está tudo certo? Responda *"sim"* para confirmar ou *"corrigir"* para reiniciar.'
    ),
    "confirm": (
        "Cadastro realizado com sucesso! \n"
        "Seu RA é: *{ra}*\n"
        "Um boleto de matrícula será enviado para {email}.\n"
        "Use seu RA para acessar o sistema a qualquer momento."
    ),
}


async def get_or_create_session(
    db: AsyncSession, tenant_id: UUID, contact_id: UUID
) -> OnboardingSession:
    """Busca ou cria uma sessão de onboarding ativa."""
    result = await db.execute(
        select(OnboardingSession).where(
            OnboardingSession.tenant_id == tenant_id,
            OnboardingSession.contact_id == contact_id,
            OnboardingSession.status == "in_progress",
        )
    )
    session = result.scalar_one_or_none()
    if session:
        return session

    session = OnboardingSession(
        tenant_id=tenant_id,
        contact_id=contact_id,
        current_step="welcome",
        collected_data={},
        status="in_progress",
    )
    db.add(session)
    await db.flush()
    return session


async def process_onboarding_step(
    db: AsyncSession,
    tenant_id: UUID,
    contact_id: UUID,
    message: str,
) -> str:
    """Processa o passo atual do onboarding e retorna a resposta."""
    session = await get_or_create_session(db, tenant_id, contact_id)
    step = session.current_step
    data = dict(session.collected_data or {})

    if step == "welcome":
        # Primeiro passo — retorna mensagem de boas-vindas
        session.current_step = "name"
        session.collected_data = data
        return STEPS["welcome"]

    elif step == "name":
        name = message.strip()
        if len(name) < 3:
            return "Nome muito curto. Por favor, informe seu nome completo:"
        data["name"] = name
        session.current_step = "cpf"
        session.collected_data = data
        return STEPS["name"].format(name=name)

    elif step == "cpf":
        cpf = re.sub(r"\D", "", message)
        if len(cpf) != 11:
            return "CPF inválido. Informe 11 dígitos numéricos:"
        # Verifica duplicata
        existing = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_id,
                Student.cpf == cpf,
            )
        )
        if existing.scalar_one_or_none():
            return (
                "Já existe um cadastro com esse CPF. "
                "Se você já é aluno, informe seu RA para se identificar."
            )
        data["cpf"] = cpf
        session.current_step = "email"
        session.collected_data = data
        return STEPS["cpf"]

    elif step == "email":
        email = message.strip().lower()
        if "@" not in email or "." not in email:
            return "E-mail inválido. Informe um e-mail válido:"
        data["email"] = email
        session.current_step = "course"
        session.collected_data = data
        return STEPS["email"]

    elif step == "course":
        course = message.strip()
        if len(course) < 3:
            return "Informe o nome do curso desejado:"
        data["course"] = course
        session.current_step = "confirm"
        session.collected_data = data
        return STEPS["course"].format(**data)

    elif step == "confirm":
        if message.strip().lower() in ("sim", "s", "confirmar", "ok"):
            # Cria registro do aluno
            ra = f"RA{uuid.uuid4().hex[:6].upper()}"
            student = Student(
                tenant_id=tenant_id,
                registration_number=ra,
                full_name=data.get("name", ""),
                cpf=data.get("cpf"),
                email=data.get("email"),
                course=data.get("course"),
                enrollment_status="pending_enrollment",
            )
            db.add(student)

            session.status = "completed"
            session.collected_data = {**data, "ra": ra}

            return STEPS["confirm"].format(ra=ra, email=data.get("email", ""))
        elif message.strip().lower() in ("corrigir", "nao", "não", "n"):
            session.current_step = "welcome"
            session.collected_data = {}
            return "Vamos recomeçar. Qual é o seu *nome completo*?"
        else:
            return 'Responda *"sim"* para confirmar ou *"corrigir"* para reiniciar.'

    return "Desculpe, não entendi. Tente novamente."
