# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

_VAPID_CONFIGURED = bool(settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY)


def _build_subscription_info(sub: "PushSubscription") -> dict:
    return {
        "endpoint": sub.endpoint,
        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
    }


def send_push_notification(
    subscription: "PushSubscription",
    title: str,
    body: str,
    url: str = "/app/dashboard",
    icon: str = "/icons/icon-192.svg",
) -> bool:
    """Send a Web Push notification to a single subscription. Returns True on success."""
    if not _VAPID_CONFIGURED:
        logger.debug("VAPID keys not configured — skipping push notification")
        return False

    try:
        from pywebpush import webpush  # type: ignore[import]

        payload = json.dumps({"title": title, "body": body, "url": url, "icon": icon})
        webpush(
            subscription_info=_build_subscription_info(subscription),
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        # 410 Gone means the subscription is no longer valid
        gone = (
            hasattr(exc, "response")
            and exc.response is not None
            and exc.response.status_code == 410
        )
        if gone:
            logger.info("Push subscription gone (410): %s", subscription.endpoint[:60])
            raise SubscriptionExpiredError(subscription.endpoint) from exc
        logger.warning("Push notification failed: %s", exc)
        return False


def send_push_to_many(
    subscriptions: list["PushSubscription"],
    title: str,
    body: str,
    url: str = "/app/dashboard",
) -> tuple[int, list[str]]:
    """Send to multiple subscriptions. Returns (sent_count, expired_endpoints)."""
    sent = 0
    expired: list[str] = []
    for sub in subscriptions:
        try:
            if send_push_notification(sub, title, body, url):
                sent += 1
        except SubscriptionExpiredError:
            expired.append(sub.endpoint)
    return sent, expired


class SubscriptionExpiredError(Exception):
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        super().__init__(f"Subscription expired: {endpoint[:60]}")
