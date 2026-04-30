from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.push_subscription import PushSubscription
from app.models.user import User

router = APIRouter(prefix="/push-subscriptions", tags=["push-subscriptions"])


class SubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class VapidKeyOut(BaseModel):
    public_key: str
    enabled: bool


@router.get("/vapid-public-key", response_model=VapidKeyOut)
async def get_vapid_public_key() -> VapidKeyOut:
    return VapidKeyOut(
        public_key=settings.VAPID_PUBLIC_KEY,
        enabled=bool(settings.VAPID_PUBLIC_KEY),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: SubscriptionIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        if body.user_agent:
            existing.user_agent = body.user_agent
        await db.commit()
        return {"status": "updated"}

    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        user_agent=body.user_agent,
    )
    db.add(sub)
    await db.commit()
    return {"status": "created"}


@router.delete("/{endpoint_hash}", status_code=status.HTTP_200_OK)
async def unsubscribe(
    endpoint_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user.id
        )
    )
    subs = result.scalars().all()
    target = next(
        (s for s in subs if hashlib.sha256(s.endpoint.encode()).hexdigest()[:16] == endpoint_hash),
        None,
    )
    if not target:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.execute(
        delete(PushSubscription).where(PushSubscription.id == target.id)
    )
    await db.commit()
    return {"status": "unsubscribed"}
