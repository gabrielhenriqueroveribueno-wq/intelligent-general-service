# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
class IGSException(Exception):
    def __init__(self, detail: str, code: str = "ERROR", status_code: int = 400):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(IGSException):
    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            detail=f"{resource} não encontrado",
            code="NOT_FOUND",
            status_code=404,
        )


class UnauthorizedError(IGSException):
    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(detail=detail, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(IGSException):
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(detail=detail, code="FORBIDDEN", status_code=403)


class ValidationError(IGSException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, code="VALIDATION_ERROR", status_code=422)


class ConflictError(IGSException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, code="CONFLICT", status_code=409)
