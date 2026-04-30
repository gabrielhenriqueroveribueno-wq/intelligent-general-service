import time

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "IGS API"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database não disponível: {e}")


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Verifica todos os componentes do sistema.
    Retorna 200 se tudo OK, 207 se parcialmente degradado, 503 se crítico.
    """
    checks: dict[str, dict] = {}
    overall_ok = True
    critical_fail = False

    # ── PostgreSQL ────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        result = await db.execute(text("SELECT version()"))
        version = result.scalar() or ""
        checks["postgres"] = {
            "status": "ok",
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "version": version.split(" ")[1] if " " in version else version[:20],
        }
    except Exception as exc:
        checks["postgres"] = {"status": "error", "error": str(exc)[:120]}
        overall_ok = False
        critical_fail = True

    # ── Redis ────────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        info = await r.info("server")
        await r.aclose()
        checks["redis"] = {
            "status": "ok",
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "version": info.get("redis_version", "?"),
        }
    except Exception as exc:
        checks["redis"] = {"status": "error", "error": str(exc)[:120]}
        overall_ok = False
        critical_fail = True

    # ── Celery workers (via Redis queue inspect) ──────────────
    t0 = time.monotonic()
    try:
        r = aioredis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        # Celery default queue
        queue_len = await r.llen("celery")
        await r.aclose()
        checks["celery"] = {
            "status": "ok",
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "queue_depth": queue_len,
        }
    except Exception as exc:
        checks["celery"] = {"status": "degraded", "error": str(exc)[:120]}
        overall_ok = False

    # ── AI Providers ─────────────────────────────────────────
    try:
        from app.services import ai_client

        circuit_states = {}
        for name, state in ai_client._circuit_states.items():
            circuit_states[name] = "open" if state.is_open else "closed"

        checks["ai_providers"] = {
            "status": "ok" if not any(v == "open" for v in circuit_states.values()) else "degraded",
            "circuits": circuit_states,
            "active_provider": settings.AI_PROVIDER,
        }
        if checks["ai_providers"]["status"] == "degraded":
            overall_ok = False
    except Exception as exc:
        checks["ai_providers"] = {"status": "unknown", "error": str(exc)[:80]}

    # ── Disk (backup dir) ────────────────────────────────────
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        free_pct = round(free / total * 100, 1)
        checks["disk"] = {
            "status": "ok" if free_pct > 10 else "warning",
            "free_pct": free_pct,
            "free_gb": round(free / 1e9, 1),
        }
        if free_pct <= 5:
            overall_ok = False
    except Exception:
        checks["disk"] = {"status": "unknown"}

    # ── Summary ───────────────────────────────────────────────
    if critical_fail:
        status_code = 503
        overall = "critical"
    elif not overall_ok:
        status_code = 207
        overall = "degraded"
    else:
        status_code = 200
        overall = "healthy"

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "checks": checks, "timestamp": time.time()},
    )
