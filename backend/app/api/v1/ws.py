"""
Endpoint WebSocket para atualizações em tempo real do painel de agentes.

Conexão: ws://host/api/v1/ws?token=<JWT_ACCESS_TOKEN>

Eventos enviados ao cliente:
  {"type": "new_message",        "tenant_id": "...", "conversation_id": "...", "intent": "...", "resolution_type": "..."}
  {"type": "conversation_closed","tenant_id": "...", "conversation_id": "..."}
  {"type": "conversation_waiting","tenant_id": "...", "conversation_id": "..."}
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.services.ws_manager import ws_manager
from app.utils.security import decode_access_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    # Autenticação via JWT no query param (headers não são suportados em WS browsers)
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        # super_admin sem tenant_id — não recebe eventos de tenant específico
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(str(tenant_id), websocket)
    try:
        # Mantém a conexão aberta aguardando mensagens do cliente (ex: ping)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(str(tenant_id), websocket)
        logger.info("WS desconectado: tenant=%s", tenant_id)
    except Exception as exc:
        logger.error("Erro WS inesperado: %s", exc)
        ws_manager.disconnect(str(tenant_id), websocket)
