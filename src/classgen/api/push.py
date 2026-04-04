"""Web Push notification subscription router.

Routes:
- GET  /api/vapid-key       Return VAPID public key
- POST /api/push/subscribe  Register a push subscription
"""

from __future__ import annotations

from fastapi import APIRouter

from classgen.api.schemas import PushSubscription
from classgen.data import save_push_subscription

router = APIRouter()


@router.get("/api/vapid-key")
async def vapid_key():
    """Return the VAPID public key for push subscription."""
    from classgen.services.notification_service import VAPID_PUBLIC_KEY

    return {"publicKey": VAPID_PUBLIC_KEY}


@router.post("/api/push/subscribe")
async def push_subscribe(sub: PushSubscription):
    """Register a push notification subscription."""
    subscription = {"endpoint": sub.endpoint, "keys": sub.keys}
    teacher_id = sub.teacher_id or sub.endpoint[:40]
    save_push_subscription(teacher_id, subscription)
    return {"ok": True}
