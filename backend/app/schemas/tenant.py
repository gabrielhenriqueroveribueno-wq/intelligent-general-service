import uuid
from typing import Optional

from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    slug: str
    whatsapp_phone: Optional[str] = None
    plan: str = "basic"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    claude_api_key: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    whatsapp_phone: Optional[str]
    plan: str
    is_active: bool

    class Config:
        from_attributes = True
