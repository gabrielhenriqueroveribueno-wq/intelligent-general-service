"""
Servico de OCR para documentos enviados via foto no WhatsApp.
Usa Claude/Gemini Vision para extrair dados de documentos.
"""

import json
import logging
from pathlib import Path

from app.services.ai_client import ai_vision

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("/app/media")

DOCUMENT_OCR_PROMPT = """Voce e um sistema de OCR e analise de documentos.
Analise a imagem enviada e extraia as informacoes em formato JSON:

{
    "document_type": "<tipo do documento: rg, cpf, comprovante_residencia, diploma, historico_escolar, boleto, contrato, outro>",
    "extracted_data": {
        // campos extraidos do documento conforme o tipo
    },
    "confidence": "<alta, media, baixa>",
    "notes": "<observacoes ou campos que nao conseguiu ler>"
}

REGRAS:
1. Responda APENAS com JSON valido.
2. Se nao conseguir ler algum campo, use null.
3. Se a imagem nao for um documento, retorne: {"document_type": "nao_identificado", "error": "Imagem nao parece ser um documento"}
4. Para RG: extraia nome, rg, data_nascimento, filiacao.
5. Para CPF: extraia nome, cpf.
6. Para comprovante de residencia: extraia nome, endereco, cep, cidade, estado.
7. Para boleto: extraia valor, vencimento, codigo_barras, beneficiario.
8. Para historico escolar: extraia nome, instituicao, curso, disciplinas com notas.
9. Para outros: extraia o maximo de texto e informacoes visiveis.
"""


async def process_document_photo(
    image_path: str,
    context: str = "",
) -> dict:
    """
    Processa foto de documento e extrai dados via IA Vision.

    Args:
        image_path: caminho da imagem no servidor
        context: contexto adicional (ex: "aluno enviou comprovante")

    Returns:
        dict com dados extraidos do documento.
    """
    full_path = (
        MEDIA_DIR / image_path.lstrip("/media/")
        if not image_path.startswith("/app")
        else Path(image_path)
    )
    if not full_path.exists():
        full_path = (
            Path(image_path) if Path(image_path).exists() else MEDIA_DIR / Path(image_path).name
        )

    if not full_path.exists():
        return {"success": False, "message": "Imagem nao encontrada no servidor."}

    image_data = full_path.read_bytes()

    ext = full_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    user_msg = "Analise este documento e extraia as informacoes."
    if context:
        user_msg += f" Contexto: {context}"

    try:
        response = await ai_vision(
            system=DOCUMENT_OCR_PROMPT,
            message=user_msg,
            image_data=image_data,
            media_type=media_type,
            max_tokens=800,
        )
    except Exception as e:
        logger.error("Erro OCR documento: %s", e)
        return {"success": False, "message": "Erro ao processar a imagem."}

    raw_text = response.text
    try:
        if "{" in raw_text:
            json_str = raw_text[raw_text.index("{") : raw_text.rindex("}") + 1]
            extracted = json.loads(json_str)
        else:
            return {"success": False, "message": "Nao foi possivel extrair dados da imagem."}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Resposta OCR nao e JSON valido: %s", raw_text[:200])
        return {"success": False, "message": "Erro ao interpretar os dados do documento."}

    if "error" in extracted:
        return {"success": False, "message": extracted["error"]}

    doc_type = extracted.get("document_type", "outro")
    data = extracted.get("extracted_data", {})
    confidence = extracted.get("confidence", "media")

    # Formata resposta legivel
    data_lines = "\n".join(f"  - *{k}*: {v}" for k, v in data.items() if v is not None)

    return {
        "success": True,
        "document_type": doc_type,
        "extracted_data": data,
        "confidence": confidence,
        "notes": extracted.get("notes", ""),
        "message": (
            f"Documento identificado: *{doc_type}*\n\n"
            f"Dados extraidos:\n{data_lines}\n\n"
            f"Confianca: *{confidence}*"
        ),
    }
