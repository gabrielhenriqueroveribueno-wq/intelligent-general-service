"""
Serviço de mídia — download e armazenamento de arquivos do WhatsApp.

Fluxo:
1. Recebe media_id do webhook
2. Chama Graph API para obter URL temporária
3. Baixa o arquivo
4. Salva localmente em /app/media/
5. Retorna URL relativa para salvar no banco

Nota: Para produção, substituir upload_to_storage() por S3/Cloudflare R2.
"""

import hashlib
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("/app/media")
GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


async def get_media_url(media_id: str, access_token: str) -> str | None:
    """Obtém a URL temporária de download de uma mídia pelo ID."""
    url = f"{GRAPH_API_BASE}/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json().get("url")
        except Exception as exc:
            logger.error("Falha ao obter URL da mídia %s: %s", media_id, exc)
            return None


async def download_media(media_url: str, access_token: str) -> bytes | None:
    """Baixa o conteúdo binário de uma URL de mídia do WhatsApp."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(media_url, headers=headers)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            logger.error("Falha ao baixar mídia: %s", exc)
            return None


async def upload_to_storage(
    content: bytes,
    media_id: str,
    mime_type: str,
) -> str | None:
    """
    Persiste o arquivo localmente e retorna o caminho relativo.
    Substituir por S3/R2 em produção.
    """
    try:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)

        # Extensão baseada no MIME type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "audio/ogg": ".ogg",
            "audio/mpeg": ".mp3",
            "video/mp4": ".mp4",
        }
        ext = ext_map.get(mime_type, ".bin")

        # Nome do arquivo: hash do conteúdo para evitar duplicatas
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        filename = f"{media_id}_{content_hash}{ext}"
        filepath = MEDIA_DIR / filename

        filepath.write_bytes(content)
        logger.info("Mídia salva: %s (%d bytes)", filename, len(content))
        return f"/media/{filename}"
    except Exception as exc:
        logger.error("Falha ao salvar mídia: %s", exc)
        return None


async def fetch_and_store_media(
    media_id: str,
    mime_type: str,
    access_token: str,
) -> str | None:
    """
    Pipeline completo: obtém URL → baixa → salva.
    Retorna a URL interna do arquivo ou None em caso de falha.
    """
    media_url = await get_media_url(media_id, access_token)
    if not media_url:
        return None

    content = await download_media(media_url, access_token)
    if not content:
        return None

    return await upload_to_storage(content, media_id, mime_type)
