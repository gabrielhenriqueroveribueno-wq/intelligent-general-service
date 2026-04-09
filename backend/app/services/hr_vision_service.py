"""
Serviço de RH com Visão Computacional — processamento de atestados médicos.

Fluxo:
1. Funcionário envia foto do atestado via WhatsApp
2. Imagem é baixada e salva via media_service
3. IA (Gemini Flash / Claude Vision) extrai: dias de afastamento, CID, médico, data
4. Sistema cria HRRequest automática e bloqueia TimeRecord nos dias correspondentes
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, HRRequest, TimeRecord
from app.services.ai_client import ai_vision

logger = logging.getLogger(__name__)

MEDICAL_CERTIFICATE_PROMPT = """Você é um sistema de OCR e análise de documentos médicos.
Analise a imagem do atestado médico e extraia as informações em formato JSON:

{
    "days_off": <número de dias de afastamento (int)>,
    "cid": "<código CID-10 se visível, ou null>",
    "doctor_name": "<nome do médico>",
    "crm": "<número do CRM se visível, ou null>",
    "start_date": "<data de início do afastamento no formato YYYY-MM-DD, ou null>",
    "clinic_name": "<nome da clínica/hospital, ou null>",
    "notes": "<observações adicionais relevantes>"
}

REGRAS:
1. Responda APENAS com JSON válido, sem texto adicional.
2. Se não conseguir ler algum campo, use null.
3. Se o documento NÃO for um atestado médico, retorne: {"error": "Documento não é um atestado médico"}
4. Extraia o número de dias com precisão (ex: "3 dias" → 3).
"""

MEDIA_DIR = Path("/app/media")


async def process_medical_certificate(
    db: AsyncSession,
    tenant_id: UUID,
    employee_id: UUID,
    image_path: str,
    access_token: str = "",
) -> dict:
    """
    Processa foto de atestado médico usando visão computacional.

    1. Lê a imagem do disco
    2. Envia para IA com visão (Gemini/Claude)
    3. Extrai dados estruturados
    4. Cria HRRequest
    5. Bloqueia TimeRecords nos dias de afastamento

    Returns:
        dict com dados extraídos e status da operação.
    """
    # 1. Load image
    full_path = (
        MEDIA_DIR / image_path.lstrip("/media/")
        if not image_path.startswith("/app")
        else Path(image_path)
    )
    if not full_path.exists():
        # Try absolute path
        full_path = (
            Path(image_path) if Path(image_path).exists() else MEDIA_DIR / Path(image_path).name
        )

    if not full_path.exists():
        return {"success": False, "message": "Imagem do atestado não encontrada no servidor."}

    image_data = full_path.read_bytes()

    # Detect media type from extension
    ext = full_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    # 2. Send to vision AI
    try:
        response = await ai_vision(
            system=MEDICAL_CERTIFICATE_PROMPT,
            message="Analise este atestado médico e extraia as informações solicitadas.",
            image_data=image_data,
            media_type=media_type,
            max_tokens=500,
        )
    except Exception as e:
        logger.error("Erro na análise de visão do atestado: %s", e)
        return {
            "success": False,
            "message": "Erro ao processar a imagem do atestado. Tente novamente.",
        }

    # 3. Parse AI response
    raw_text = response.text
    try:
        if "{" in raw_text:
            json_str = raw_text[raw_text.index("{") : raw_text.rindex("}") + 1]
            extracted = json.loads(json_str)
        else:
            return {"success": False, "message": "Não foi possível extrair dados da imagem."}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Resposta de visão não é JSON válido: %s", raw_text[:200])
        return {"success": False, "message": "Erro ao interpretar os dados do atestado."}

    if "error" in extracted:
        return {"success": False, "message": extracted["error"]}

    days_off = extracted.get("days_off")
    cid = extracted.get("cid")
    doctor_name = extracted.get("doctor_name", "")
    start_date_str = extracted.get("start_date")

    if not days_off or not isinstance(days_off, int) or days_off < 1:
        return {
            "success": False,
            "message": "Não foi possível identificar os dias de afastamento no atestado.",
        }

    # Determine start date
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            start_date = date.today()
    else:
        start_date = date.today()

    # 4. Verify employee exists
    emp_result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.tenant_id == tenant_id,
        )
    )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        return {"success": False, "message": "Funcionário não encontrado."}

    # 5. Create HRRequest
    cid_text = f" (CID: {cid})" if cid else ""
    description = (
        f"Atestado médico processado automaticamente via IA.\n"
        f"Médico: {doctor_name}\n"
        f"CID: {cid or 'não identificado'}\n"
        f"Período: {start_date.strftime('%d/%m/%Y')} a "
        f"{(start_date + timedelta(days=days_off - 1)).strftime('%d/%m/%Y')}\n"
        f"Dias de afastamento: {days_off}\n"
        f"Clínica: {extracted.get('clinic_name', 'não identificada')}\n"
        f"Imagem: {image_path}"
    )

    hr_request = HRRequest(
        tenant_id=tenant_id,
        employee_id=employee_id,
        request_type="medical_certificate",
        description=description,
        status="approved",  # auto-approved by AI
        response_text=f"Atestado de {days_off} dia(s){cid_text} registrado automaticamente.",
    )
    db.add(hr_request)
    await db.flush()

    # 6. Block TimeRecords for the leave period
    blocked_dates = []
    for i in range(days_off):
        leave_date = start_date + timedelta(days=i)

        # Check if there's already a record for this date
        existing = await db.execute(
            select(TimeRecord).where(
                TimeRecord.tenant_id == tenant_id,
                TimeRecord.employee_id == employee_id,
                TimeRecord.record_date == leave_date,
            )
        )
        record = existing.scalar_one_or_none()

        if record:
            record.status = "medical_leave"
            record.total_hours = None
            record.clock_in = None
            record.clock_out = None
        else:
            new_record = TimeRecord(
                tenant_id=tenant_id,
                employee_id=employee_id,
                record_date=leave_date,
                status="medical_leave",
            )
            db.add(new_record)

        blocked_dates.append(str(leave_date))

    await db.flush()

    return {
        "success": True,
        "employee_name": employee.full_name,
        "days_off": days_off,
        "cid": cid,
        "doctor_name": doctor_name,
        "start_date": str(start_date),
        "end_date": str(start_date + timedelta(days=days_off - 1)),
        "blocked_dates": blocked_dates,
        "hr_request_id": str(hr_request.id),
        "tokens_used": response.tokens_used,
        "provider_used": response.provider_used,
        "message": (
            f"Atestado médico processado com sucesso para {employee.full_name}! ✅\n\n"
            f"📋 Dados extraídos:\n"
            f"• Médico: {doctor_name}\n"
            f"• CID: {cid or 'não identificado'}\n"
            f"• Afastamento: {days_off} dia(s)\n"
            f"• Período: {start_date.strftime('%d/%m/%Y')} a "
            f"{(start_date + timedelta(days=days_off - 1)).strftime('%d/%m/%Y')}\n\n"
            f"O registro de ponto foi automaticamente atualizado. "
            f"Solicitação HR registrada com status *aprovado*."
        ),
    }
