import hashlib
import hmac

from app.config import settings


def verify_webhook_signature(payload: bytes, signature_header: str) -> bool:
    """Verifica a assinatura HMAC-SHA256 do webhook da Meta."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[7:]  # Remove "sha256="

    computed = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_signature)
