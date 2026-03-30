"""
Serviço de transcrição de áudio do WhatsApp usando IA.
"""

import base64
import logging

from app.services.ai_client import ai_complete

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """
    Transcreve áudio usando o provider de IA configurado.
    Retorna o texto transcrito.
    """
    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")

    system = (
        "Você é um transcritor de áudio. "
        "Transcreva o áudio a seguir para texto em português brasileiro. "
        "Retorne APENAS o texto transcrito, sem explicações adicionais."
    )
    message = f"Transcreva este áudio (formato: {mime_type}, codificado em base64):\n\n{audio_b64}"

    try:
        result = await ai_complete(
            system=system,
            message=message,
            max_tokens=1000,
        )
        logger.info("Áudio transcrito com sucesso (%d caracteres)", len(result.text))
        return result.text

    except Exception as e:
        logger.error("Erro na transcrição de áudio: %s", e)
        return "[Não foi possível transcrever o áudio. Tente enviar em texto.]"
