from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WhatsAppMessageText(BaseModel):
    body: str


class WhatsAppMessage(BaseModel):
    id: str
    from_: str
    timestamp: str
    type: str
    text: Optional[WhatsAppMessageText] = None

    class Config:
        populate_by_name = True
        fields = {"from_": "from"}


class WhatsAppStatus(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str


class WhatsAppContact(BaseModel):
    profile: Dict[str, str]
    wa_id: str


class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None


class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]
