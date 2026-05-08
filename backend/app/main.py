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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    from app.services.ws_manager import ws_manager

    logger.info("IGS API iniciando...")
    redis_task = asyncio.create_task(ws_manager.start_redis_listener())
    yield
    redis_task.cancel()
    logger.info("IGS API encerrando...")


def create_app() -> FastAPI:
    # Em producao, Swagger fica em /api/docs (atras do reverse proxy /api/*)
    # Em dev, fica direto em /docs
    if settings.is_production:
        docs_url = "/api/docs"
        redoc_url = "/api/redoc"
        openapi_url = "/api/openapi.json"
    else:
        docs_url = "/docs"
        redoc_url = "/redoc"
        openapi_url = "/openapi.json"

    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

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
