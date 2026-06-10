import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_type: str
    content: str
    message_type: str
    intent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    channel: str
    status: str
    context_type: Optional[str]
    started_at: datetime
    last_message_at: Optional[datetime]
    satisfaction_score: Optional[int]
    last_sentiment: Optional[str] = None  # positive, neutral, negative
    assigned_agent_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

    @field_validator("messages", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v: object) -> object:
        # Relação `messages` pode vir None quando não foi eager-loaded no ORM.
        # O endpoint preenche as mensagens ordenadas depois — aqui só evitamos
        # que o model_validate(conv) quebre ao ler conv.messages == None.
        return v if v is not None else []


class AgentMessageCreate(BaseModel):
    content: str


class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
    page: int
    size: int
