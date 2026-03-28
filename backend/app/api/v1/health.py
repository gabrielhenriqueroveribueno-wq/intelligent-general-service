from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=f"Database não disponível: {e}")
