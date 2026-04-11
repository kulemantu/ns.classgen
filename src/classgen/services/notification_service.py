"""Web Push notification system for ClassGen.

Sends browser notifications to teachers when students submit quizzes,
when lesson generation completes, or other events worth interrupting for.
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from pywebpush import WebPushException, webpush

from classgen.data.push import (
    get_push_subscriptions,
    remove_push_subscription,
)

load_dotenv()

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS = {"sub": os.environ.get("VAPID_CONTACT", "mailto:admin@classgen.ng")}


def send_push(teacher_id: str, title: str, body: str, url: str = "", tag: str = "") -> int:
    """Send a push notification to all of a teacher's subscriptions.

    Returns the number of successful deliveries.
    """
    if not VAPID_PRIVATE_KEY:
        print(f"[local] Push notification -> {teacher_id}: {title} - {body}")
        return 0

    subscriptions = get_push_subscriptions(teacher_id)
    if not subscriptions:
        return 0

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "url": url,
            "tag": tag,
        }
    )

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
                # Subscription expired or invalid -- clean up
                remove_push_subscription(sub.get("endpoint", ""))
            else:
                print(f"Push error: {e}")
    return sent


def notify_quiz_submission(
    teacher_id: str,
    homework_code: str,
    student_name: str,
    score: int,
    total: int,
    base_url: str = "",
) -> int:
    """Send a push notification when a student submits a quiz."""
    return send_push(
        teacher_id=teacher_id,
        title=f"Quiz submitted: {homework_code}",
        body=f"{student_name} scored {score}/{total}",
        url=f"{base_url}/h/{homework_code}/results",
        tag=f"quiz-{homework_code}",
    )
