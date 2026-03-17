"""Web Push notification system for ClassGen.

Sends browser notifications to teachers when students submit quizzes,
when lesson generation completes, or other events worth interrupting for.
"""

import os
import json
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv

load_dotenv()

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS = {"sub": os.environ.get("VAPID_CONTACT", "mailto:admin@classgen.ng")}

# In-memory subscription store (keyed by teacher identifier)
_mem_subscriptions: dict[str, list[dict]] = {}


def save_push_subscription(teacher_id: str, subscription: dict) -> bool:
    """Save a push subscription for a teacher (thread_id or phone)."""
    from db import supabase
    endpoint = subscription.get("endpoint", "")
    if not endpoint:
        return False

    if not supabase:
        subs = _mem_subscriptions.setdefault(teacher_id, [])
        # Avoid duplicates
        if not any(s.get("endpoint") == endpoint for s in subs):
            subs.append(subscription)
        print(f"[local] Saved push subscription for {teacher_id}")
        return True
    try:
        supabase.table("push_subscriptions").upsert({
            "teacher_id": teacher_id,
            "endpoint": endpoint,
            "subscription": subscription,
        }, on_conflict="endpoint").execute()
        return True
    except Exception as e:
        print(f"Error saving push subscription: {e}")
        return False


def get_push_subscriptions(teacher_id: str) -> list[dict]:
    """Get all push subscriptions for a teacher."""
    from db import supabase
    if not supabase:
        return _mem_subscriptions.get(teacher_id, [])
    try:
        response = (
            supabase.table("push_subscriptions")
            .select("subscription")
            .eq("teacher_id", teacher_id)
            .execute()
        )
        return [r["subscription"] for r in response.data]
    except Exception as e:
        print(f"Error getting push subscriptions: {e}")
        return []


def remove_push_subscription(endpoint: str):
    """Remove a subscription (e.g., when push fails with 410 Gone)."""
    from db import supabase
    if not supabase:
        for subs in _mem_subscriptions.values():
            subs[:] = [s for s in subs if s.get("endpoint") != endpoint]
        return
    try:
        supabase.table("push_subscriptions").delete().eq("endpoint", endpoint).execute()
    except Exception as e:
        print(f"Error removing push subscription: {e}")


def send_push(teacher_id: str, title: str, body: str,
              url: str = "", tag: str = "") -> int:
    """Send a push notification to all of a teacher's subscriptions.

    Returns the number of successful deliveries.
    """
    if not VAPID_PRIVATE_KEY:
        print(f"[local] Push notification -> {teacher_id}: {title} - {body}")
        return 0

    subscriptions = get_push_subscriptions(teacher_id)
    if not subscriptions:
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "tag": tag,
    })

    sent = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            sent += 1
        except WebPushException as e:
            if "410" in str(e) or "404" in str(e):
                # Subscription expired or invalid — clean up
                remove_push_subscription(sub.get("endpoint", ""))
            else:
                print(f"Push error: {e}")
    return sent


def notify_quiz_submission(teacher_id: str, homework_code: str,
                           student_name: str, score: int, total: int,
                           base_url: str = "") -> int:
    """Send a push notification when a student submits a quiz."""
    return send_push(
        teacher_id=teacher_id,
        title=f"Quiz submitted: {homework_code}",
        body=f"{student_name} scored {score}/{total}",
        url=f"{base_url}/h/{homework_code}/results",
        tag=f"quiz-{homework_code}",
    )
