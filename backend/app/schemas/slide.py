"""Schemas para o sistema de slides IA."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Template ─────────────────────────────────────────────────────────────────


class SlideTemplateCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    template_rules: dict = Field(
        ...,
        json_schema_extra={
            "example": {
                "colors": {
                    "primary": "#1B3A5C",
                    "secondary": "#E8B931",
                    "background": "#FFFFFF",
                    "text": "#333333",
                },
                "fonts": {
                    "title": "Montserrat Bold",
                    "body": "Open Sans",
                    "size_title": 32,
                    "size_body": 18,
                },
                "layout": {
                    "logo_position": "top-right",
                    "footer_text": "Colégio Anchieta",
                    "max_bullets_per_slide": 6,
                    "include_slide_numbers": True,
                },
            }
        },
    )
    example_content: Optional[str] = None
    is_default: bool = False


class SlideTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    template_rules: Optional[dict] = None
    example_content: Optional[str] = None
    is_default: Optional[bool] = None


class SlideTemplateResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    template_rules: dict
    example_content: Optional[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Geração / Atualização ────────────────────────────────────────────────────


class SlideGenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        json_schema_extra={"example": "Crie uma aula sobre fotossíntese para o 3º ano do ensino médio, com 8 slides"},
    )
    subject: str = Field(
        ...,
        max_length=200,
        json_schema_extra={"example": "Biologia"},
    )
    template_id: Optional[UUID] = Field(
        None, description="ID do template. Se omitido, usa o template padrão."
    )
    num_slides: Optional[int] = Field(
        None, ge=3, le=30, description="Número desejado de slides (3-30)"
    )


class SlideUpdateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        json_schema_extra={"example": "Adicione um slide sobre o ciclo de Calvin após o slide 4"},
    )


# ── Presentation ─────────────────────────────────────────────────────────────


class SlideContent(BaseModel):
    """Estrutura de um slide individual."""

    slide_number: int
    title: str
    content: list[str] = Field(default_factory=list, description="Bullets / parágrafos")
    notes: Optional[str] = Field(None, description="Notas do professor")
    layout: str = Field(default="default", description="default | title | two_columns | image")


class SlidePresentationResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    template_id: Optional[UUID]
    title: str
    subject: str
    prompt_used: str
    slides_content: list[dict]
    status: str
    version: int
    total_slides: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SlidePresentationListResponse(BaseModel):
    items: list[SlidePresentationResponse]
    total: int
    page: int
    size: int


# ── Generation Log ───────────────────────────────────────────────────────────


class SlideGenerationLogResponse(BaseModel):
    id: UUID
    prompt: str
    action: str
    tokens_used: int
    ai_provider: str
    created_at: datetime

    model_config = {"from_attributes": True}
