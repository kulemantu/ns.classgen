"""Outbound Twilio messaging for ClassGen.

Handles proactive messages to teachers and parents (not webhook responses).
Used for: quiz result summaries, parent digests, study mode replies.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
_from_number = os.environ.get("TWILIO_PHONE_NUMBER", "")

_client = None
if _account_sid and _auth_token:
    try:
        from twilio.rest import Client
        _client = Client(_account_sid, _auth_token)
    except Exception as e:
        print(f"Warning: Failed to initialize Twilio client: {e}")
else:
    print("Twilio outbound not configured (TWILIO_ACCOUNT_SID/AUTH_TOKEN missing).")


def send_whatsapp(to: str, body: str) -> bool:
    """Send a WhatsApp message. Returns True on success."""
    if not _client or not _from_number:
        print(f"[local] Would send WhatsApp to {to}: {body[:80]}...")
        return False
    try:
        to_wa = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        from_wa = (
            _from_number if _from_number.startswith("whatsapp:")
            else f"whatsapp:{_from_number}"
        )
        _client.messages.create(body=body, from_=from_wa, to=to_wa)
        return True
    except Exception as e:
        print(f"Error sending WhatsApp to {to}: {e}")
        return False


def send_quiz_summary(teacher_phone: str, homework_code: str,
                      total_submissions: int, avg_score: float,
                      total_questions: int, base_url: str) -> bool:
    """Send a quiz results summary to a teacher after students submit."""
    body = (
        f"*Quiz results for {homework_code}*\n\n"
        f"Students: {total_submissions}\n"
        f"Average: {avg_score:.1f}/{total_questions}\n\n"
        f"Full details: {base_url}/h/{homework_code}/results"
    )
    return send_whatsapp(teacher_phone, body)


def send_parent_digest(parent_phone: str, teacher_name: str,
                       class_name: str, lessons: list[str],
                       homework: str) -> bool:
    """Send a weekly digest to a parent."""
    lesson_list = ", ".join(lessons) if lessons else "No lessons this week"
    body = (
        f"*Weekly update from {teacher_name} -- {class_name}*\n\n"
        f"This week: {lesson_list}\n"
        f"Homework: {homework}\n\n"
        f"Powered by ClassGen"
    )
    return send_whatsapp(parent_phone, body)
