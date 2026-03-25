import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TicketCreate(BaseModel):
    subject: str
    category: Optional[str] = None
    description: Optional[str] = None
    priority: str = "medium"
    contact_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    category: Optional[str] = None


class TicketCommentCreate(BaseModel):
    content: str
    is_internal: bool = False


class TicketCommentResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    id: uuid.UUID
    protocol_number: str
    subject: str
    category: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[uuid.UUID]
    sla_deadline: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketResponse):
    description: Optional[str]
    comments: List[TicketCommentResponse] = []


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    size: int
