"""
Serviço de geração e atualização de slides via IA.

Usa o ai_client unificado para gerar apresentações seguindo
o padrão institucional armazenado em SlideTemplate.
"""

import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.slide import SlideGenerationLog, SlidePresentation, SlideTemplate
from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)


def _build_template_context(template: SlideTemplate) -> str:
    """Monta o contexto do template para o system prompt."""
    rules = template.template_rules or {}
    colors = rules.get("colors", {})
    fonts = rules.get("fonts", {})
    layout = rules.get("layout", {})

    parts = [
        f"TEMPLATE: {template.name}",
        "",
        "PALETA DE CORES:",
        f"  - Primária: {colors.get('primary', '#1B3A5C')}",
        f"  - Secundária: {colors.get('secondary', '#E8B931')}",
        f"  - Fundo: {colors.get('background', '#FFFFFF')}",
        f"  - Texto: {colors.get('text', '#333333')}",
        "",
        "TIPOGRAFIA:",
        f"  - Título: {fonts.get('title', 'Montserrat Bold')} ({fonts.get('size_title', 32)}pt)",
        f"  - Corpo: {fonts.get('body', 'Open Sans')} ({fonts.get('size_body', 18)}pt)",
        "",
        "LAYOUT:",
        f"  - Logo: {layout.get('logo_position', 'top-right')}",
        f"  - Rodapé: {layout.get('footer_text', '')}",
        f"  - Máx. bullets por slide: {layout.get('max_bullets_per_slide', 6)}",
        f"  - Numeração de slides: {'Sim' if layout.get('include_slide_numbers', True) else 'Não'}",
    ]

    if template.example_content:
        parts.extend(["", "EXEMPLO DE SLIDES ANTERIORES:", template.example_content])

    return "\n".join(parts)


SYSTEM_PROMPT_GENERATE = """Você é um assistente especializado em criar apresentações de slides educacionais.
Você DEVE seguir rigorosamente o padrão visual da instituição descrito abaixo.

{template_context}

REGRAS:
1. Cada slide deve ter: título claro, conteúdo em bullets (máximo {max_bullets} por slide), e notas para o professor
2. O primeiro slide deve ser a capa com título da aula e disciplina
3. O último slide deve ser "Resumo" ou "Referências"
4. Use linguagem adequada ao nível escolar indicado
5. Inclua exemplos práticos e perguntas para reflexão quando apropriado
6. Mantenha consistência visual descrita no template

FORMATO DE RESPOSTA (JSON válido, sem markdown):
{{
  "title": "Título da Apresentação",
  "slides": [
    {{
      "slide_number": 1,
      "title": "Título do Slide",
      "content": ["bullet 1", "bullet 2"],
      "notes": "Notas para o professor",
      "layout": "title"
    }}
  ]
}}

Layouts possíveis: "title" (capa), "default" (conteúdo padrão), "two_columns" (comparação), "image" (slide para imagem/diagrama).
"""

SYSTEM_PROMPT_UPDATE = """Você é um assistente especializado em atualizar apresentações de slides educacionais.
Você DEVE manter o padrão visual da instituição e a consistência com os slides existentes.

{template_context}

SLIDES ATUAIS:
{current_slides}

REGRAS:
1. Mantenha a numeração sequencial correta
2. Preserve o estilo e tom dos slides existentes
3. Adicione, remova ou modifique slides conforme solicitado
4. Mantenha o slide de capa e o slide final (resumo/referências)
5. Cada slide: título, bullets (máximo {max_bullets}), notas do professor

FORMATO DE RESPOSTA (JSON válido, sem markdown — retorne TODOS os slides, incluindo os não modificados):
{{
  "title": "Título da Apresentação",
  "slides": [
    {{
      "slide_number": 1,
      "title": "Título do Slide",
      "content": ["bullet 1", "bullet 2"],
      "notes": "Notas para o professor",
      "layout": "title"
    }}
  ]
}}
"""


async def _get_default_template(db: AsyncSession, tenant_id: UUID) -> SlideTemplate | None:
    """Busca o template padrão do tenant."""
    result = await db.execute(
        select(SlideTemplate).where(
            SlideTemplate.tenant_id == tenant_id,
            SlideTemplate.is_default.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def _get_template(
    db: AsyncSession, tenant_id: UUID, template_id: UUID | None
) -> SlideTemplate | None:
    """Busca template por ID ou retorna o padrão."""
    if template_id:
        result = await db.execute(
            select(SlideTemplate).where(
                SlideTemplate.id == template_id,
                SlideTemplate.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()
    return await _get_default_template(db, tenant_id)


def _parse_ai_response(text: str) -> dict:
    """Extrai JSON da resposta da IA, removendo markdown se necessário."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # remove ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


async def generate_slides(
    db: AsyncSession,
    tenant_id: UUID,
    teacher_id: UUID,
    prompt: str,
    subject: str,
    template_id: UUID | None = None,
    num_slides: int | None = None,
) -> SlidePresentation:
    """Gera uma nova apresentação de slides via IA."""

    template = await _get_template(db, tenant_id, template_id)
    max_bullets = 6
    template_context = "Nenhum template definido — use um estilo limpo e profissional."

    if template:
        template_context = _build_template_context(template)
        max_bullets = template.template_rules.get("layout", {}).get("max_bullets_per_slide", 6)

    system = SYSTEM_PROMPT_GENERATE.format(
        template_context=template_context,
        max_bullets=max_bullets,
    )

    user_message = f"Disciplina: {subject}\n\n{prompt}"
    if num_slides:
        user_message += f"\n\nGere exatamente {num_slides} slides."

    response = await ai_complete(system=system, message=user_message, max_tokens=4096)

    parsed = _parse_ai_response(response.text)
    slides = parsed.get("slides", [])

    presentation = SlidePresentation(
        tenant_id=tenant_id,
        teacher_id=teacher_id,
        template_id=template.id if template else None,
        title=parsed.get("title", f"Aula de {subject}"),
        subject=subject,
        prompt_used=prompt,
        slides_content=slides,
        status="draft",
        version=1,
        total_slides=len(slides),
    )
    db.add(presentation)
    await db.flush()

    log = SlideGenerationLog(
        tenant_id=tenant_id,
        teacher_id=teacher_id,
        presentation_id=presentation.id,
        prompt=prompt,
        action="create",
        tokens_used=response.tokens_used,
        ai_provider=settings.AI_PROVIDER,
    )
    db.add(log)

    return presentation


async def update_slides(
    db: AsyncSession,
    presentation: SlidePresentation,
    prompt: str,
    tenant_id: UUID,
    teacher_id: UUID,
) -> SlidePresentation:
    """Atualiza uma apresentação existente com base em novo prompt."""

    template = await _get_template(db, tenant_id, presentation.template_id)
    max_bullets = 6
    template_context = "Sem template específico."

    if template:
        template_context = _build_template_context(template)
        max_bullets = template.template_rules.get("layout", {}).get("max_bullets_per_slide", 6)

    current_slides_json = json.dumps(presentation.slides_content, ensure_ascii=False, indent=2)

    system = SYSTEM_PROMPT_UPDATE.format(
        template_context=template_context,
        current_slides=current_slides_json,
        max_bullets=max_bullets,
    )

    response = await ai_complete(system=system, message=prompt, max_tokens=4096)

    parsed = _parse_ai_response(response.text)
    slides = parsed.get("slides", [])

    presentation.slides_content = slides
    presentation.total_slides = len(slides)
    presentation.version += 1
    presentation.title = parsed.get("title", presentation.title)

    log = SlideGenerationLog(
        tenant_id=tenant_id,
        teacher_id=teacher_id,
        presentation_id=presentation.id,
        prompt=prompt,
        action="update",
        tokens_used=response.tokens_used,
        ai_provider=settings.AI_PROVIDER,
    )
    db.add(log)

    return presentation


async def get_template_stats(db: AsyncSession, tenant_id: UUID) -> dict:
    """Estatísticas de uso dos templates."""
    total_presentations = await db.scalar(
        select(func.count(SlidePresentation.id)).where(
            SlidePresentation.tenant_id == tenant_id
        )
    )
    total_tokens = await db.scalar(
        select(func.coalesce(func.sum(SlideGenerationLog.tokens_used), 0)).where(
            SlideGenerationLog.tenant_id == tenant_id
        )
    )
    return {
        "total_presentations": total_presentations or 0,
        "total_tokens_used": total_tokens or 0,
    }
