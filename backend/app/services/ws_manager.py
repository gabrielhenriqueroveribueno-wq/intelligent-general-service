# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
WebSocket Manager — gerencia conexões ativas e broadcast via Redis pub/sub.

Arquitetura:
  - Celery worker publica eventos em `igs:ws_events` (Redis pub/sub)
  - FastAPI background task escuta o canal e chama broadcast_to_tenant()
  - broadcast_to_tenant() entrega o payload a todos os WS do tenant
"""

import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)

REDIS_CHANNEL = "igs:ws_events"


class WebSocketManager:
    def __init__(self):
        # tenant_id (str) → lista de WebSockets ativos
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, tenant_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(tenant_id, []).append(websocket)
        logger.info(
            "WS conectado: tenant=%s total=%d",
            tenant_id,
            len(self._connections[tenant_id]),
        )

    def disconnect(self, tenant_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(tenant_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(tenant_id, None)

    async def broadcast_to_tenant(self, tenant_id: str, payload: dict) -> None:
        conns = list(self._connections.get(tenant_id, []))
        if not conns:
            return
        message = json.dumps(payload, default=str)
        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(tenant_id, ws)

    async def start_redis_listener(self) -> None:
        """
        Background task que subscreve ao canal Redis e repassa eventos
        para os clientes WS conectados. Reinicia automaticamente em caso de erro.
        """
        import redis.asyncio as aioredis

        from app.config import settings

        while True:
            try:
                r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(REDIS_CHANNEL)
                logger.info("WS Redis listener ativo no canal '%s'", REDIS_CHANNEL)

                async for raw in pubsub.listen():
                    if raw.get("type") != "message":
                        continue
                    try:
                        data = json.loads(raw["data"])
                        tenant_id = data.get("tenant_id")
                        if tenant_id:
                            await self.broadcast_to_tenant(str(tenant_id), data)
                    except Exception as exc:
                        logger.error("Erro ao processar mensagem WS: %s", exc)
            except asyncio.CancelledError:
                logger.info("WS Redis listener encerrado")
                return
            except Exception as exc:
                logger.error("WS Redis listener caiu (%s), reconectando em 5s...", exc)
                await asyncio.sleep(5)


ws_manager = WebSocketManager()
