# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
import asyncio
import logging
from contextlib import asynccontextmanager

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    _SENTRY_AVAILABLE = True
except ImportError:
    _SENTRY_AVAILABLE = False

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.metrics_middleware import setup_metrics
from app.middleware.plan_limit_middleware import PlanLimitMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.utils.exceptions import IGSException

logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    if not _SENTRY_AVAILABLE or not settings.SENTRY_DSN:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        release=settings.APP_VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
        ],
        send_default_pii=False,
    )
    logger.info("Sentry inicializado (env=%s)", settings.APP_ENV)


_init_sentry()


def _validate_production_secrets() -> None:
    """Fail-closed: impede subir em producao com secrets default/fracos.

    Evita o cenario catastrofico de rodar prod com `change-me-jwt-secret`,
    o que permitiria a qualquer um forjar JWTs de admin.
    """
    if not settings.is_production:
        return

    problems: list[str] = []
    if settings.JWT_SECRET_KEY in ("", "change-me-jwt-secret") or len(settings.JWT_SECRET_KEY) < 32:
        problems.append("JWT_SECRET_KEY ausente, default ou curto (<32 chars)")
    if settings.APP_SECRET_KEY in ("", "change-me-in-production"):
        problems.append("APP_SECRET_KEY ausente ou default")
    if not settings.ENCRYPTION_KEY:
        problems.append("ENCRYPTION_KEY ausente (Fernet)")
    if not settings.WHATSAPP_APP_SECRET:
        problems.append("WHATSAPP_APP_SECRET ausente (verificacao HMAC do webhook)")

    if problems:
        raise RuntimeError("Configuracao insegura para producao: " + "; ".join(problems))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    from app.services.ws_manager import ws_manager

    _validate_production_secrets()
    logger.info("IGS API iniciando...")
    redis_task = asyncio.create_task(ws_manager.start_redis_listener())
    yield
    redis_task.cancel()
    logger.info("IGS API encerrando...")


def _register_docs_endpoints(app: FastAPI, openapi_url: str) -> None:
    """
    Serve Swagger UI e ReDoc com assets de unpkg.com (mais confiavel
    que jsdelivr em redes corporativas/operadoras BR que bloqueiam CDN).
    """
    from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

    docs_path = "/api/docs" if settings.is_production else "/docs"
    redoc_path = "/api/redoc" if settings.is_production else "/redoc"

    @app.get(docs_path, include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{settings.APP_TITLE} - Swagger UI",
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css",
            swagger_favicon_url="/favicon.ico",
        )

    @app.get(redoc_path, include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=openapi_url,
            title=f"{settings.APP_TITLE} - ReDoc",
            redoc_js_url="https://unpkg.com/redoc@2.1.5/bundles/redoc.standalone.js",
            redoc_favicon_url="/favicon.ico",
            with_google_fonts=False,
        )


def create_app() -> FastAPI:
    # Em producao, Swagger fica em /api/docs (atras do reverse proxy /api/*)
    # Em dev, fica direto em /docs
    if settings.is_production:
        openapi_url = "/api/openapi.json"
    else:
        openapi_url = "/openapi.json"

    # docs_url/redoc_url=None: registramos endpoints customizados abaixo
    # usando CDN unpkg.com (mais confiavel que jsdelivr em redes restritas BR)
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    _register_docs_endpoints(app, openapi_url)

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL.replace("/0", "/3"))
    app.add_middleware(PlanLimitMiddleware, redis_url=settings.REDIS_URL.replace("/0", "/3"))

    # ── Prometheus ────────────────────────────────────────────
    if settings.PROMETHEUS_ENABLED:
        setup_metrics(app)

    # ── Rotas ─────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Exception Handlers ────────────────────────────────────
    @app.exception_handler(IGSException)
    async def igs_exception_handler(request: Request, exc: IGSException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Erro não tratado: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor", "code": "INTERNAL_ERROR"},
        )

    return app


app = create_app()
