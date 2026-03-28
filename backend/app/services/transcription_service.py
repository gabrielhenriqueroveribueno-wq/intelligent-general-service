"""
Serviço de transcrição de áudio do WhatsApp usando Claude API.
"""

import base64
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """
    Transcreve áudio usando Claude API (envio como base64).
    Retorna o texto transcrito.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    audio_b64 = base64.standard_b64encode(audio_bytes).decode("utf-8")

    try:
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1000,
            system=(
                "Você é um transcritor de áudio. "
                "Transcreva o áudio a seguir para texto em português brasileiro. "
                "Retorne APENAS o texto transcrito, sem explicações adicionais."
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Transcreva este áudio (formato: {mime_type}, "
                                f"codificado em base64):\n\n{audio_b64}"
                            ),
                        },
                    ],
                }
            ],
        )
        transcription = response.content[0].text.strip()
        logger.info("Áudio transcrito com sucesso (%d caracteres)", len(transcription))
        return transcription

    except anthropic.APIError as e:
        logger.error("Erro na transcrição de áudio: %s", e)
        return "[Não foi possível transcrever o áudio. Tente enviar em texto.]"
