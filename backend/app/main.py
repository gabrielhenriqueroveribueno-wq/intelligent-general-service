import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import api_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.metrics_middleware import setup_metrics
from app.utils.exceptions import IGSException

logger = logging.getLogger(__name__)


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
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
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
