"""
Cliente unificado de IA — suporta Anthropic (Claude), Google (Gemini) e Groq (Llama).

Uso:
    result = await ai_complete(system_prompt, user_message, max_tokens=1024)
    print(result.text, result.tokens_used)
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    text: str
    tokens_used: int


async def ai_complete(
    system: str,
    message: str,
    max_tokens: int = 1024,
    api_key: Optional[str] = None,
) -> AIResponse:
    """
    Envia prompt para o provider configurado (groq, gemini ou anthropic).
    Retorna AIResponse(text, tokens_used).
    """
    provider = settings.AI_PROVIDER.lower()

    if provider == "groq":
        return await _groq_complete(system, message, max_tokens)
    elif provider == "gemini":
        return await _gemini_complete(system, message, max_tokens)
    else:
        return await _anthropic_complete(system, message, max_tokens, api_key)


async def _anthropic_complete(
    system: str,
    message: str,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> AIResponse:
    import anthropic

    effective_key = api_key or settings.ANTHROPIC_API_KEY
    client = anthropic.AsyncAnthropic(api_key=effective_key)

    try:
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": message}],
        )
        text = response.content[0].text.strip()
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return AIResponse(text=text, tokens_used=tokens)

    except anthropic.APIError as e:
        logger.error("Erro Anthropic API: %s", e)
        raise


async def _groq_complete(
    system: str,
    message: str,
    max_tokens: int,
) -> AIResponse:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
        )
        text = response.choices[0].message.content.strip()
        tokens = 0
        if response.usage:
            tokens = (response.usage.prompt_tokens or 0) + (response.usage.completion_tokens or 0)
        return AIResponse(text=text, tokens_used=tokens)

    except Exception as e:
        logger.error("Erro Groq API: %s", e)
        raise


async def _gemini_complete(
    system: str,
    message: str,
    max_tokens: int,
) -> AIResponse:
    import google.generativeai as genai

    genai.configure(api_key=settings.GOOGLE_API_KEY)

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
        ),
    )

    try:
        response = await model.generate_content_async(message)
        text = response.text.strip()

        tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = (
                getattr(response.usage_metadata, "prompt_token_count", 0)
                + getattr(response.usage_metadata, "candidates_token_count", 0)
            )

        return AIResponse(text=text, tokens_used=tokens)

    except Exception as e:
        logger.error("Erro Gemini API: %s", e)
        raise
