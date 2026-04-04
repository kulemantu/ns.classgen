"""Subscription and usage-tracking data access for ClassGen.

Handles subscription CRUD and usage logging with in-memory fallback.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from classgen.data.client import supabase

# --- In-memory fallback stores ---

_mem_subscriptions: dict[str, dict] = {}
_mem_usage: dict[str, list] = {}


# --- Usage tracking ---


def log_usage(teacher_phone: str, action: str = "lesson"):
    """Log a usage event (lesson generated, quiz created, etc.)."""
    record = {
        "teacher_phone": teacher_phone,
        "action": action,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        _mem_usage.setdefault(teacher_phone, []).append(record)
        return
    try:
        supabase.table("usage_log").insert(record).execute()
    except Exception as e:
        print(f"Error logging usage: {e}")


def get_weekly_usage(teacher_phone: str) -> int:
    """Count lessons generated this week."""
    now = datetime.now(timezone.utc)
    # Monday of this week (safe across month boundaries)
    week_start = (
        now.replace(hour=0, minute=0, second=0, microsecond=0)
        - timedelta(days=now.weekday())
    )
    week_start_iso = week_start.isoformat()

    if not supabase:
        events = _mem_usage.get(teacher_phone, [])
        return sum(1 for e in events
                   if e.get("action") == "lesson"
                   and (e.get("created_at") or "") >= week_start_iso)
    try:
        response = (
            supabase.table("usage_log")
            .select("id", count="exact")
            .eq("teacher_phone", teacher_phone)
            .eq("action", "lesson")
            .gte("created_at", week_start_iso)
            .execute()
        )
        return response.count or 0
    except Exception as e:
        print(f"Error getting usage: {e}")
        return 0


# --- Subscriptions ---


def get_subscription(teacher_phone: str) -> dict:
    """Get a teacher's subscription tier. Defaults to free."""
    if not supabase:
        return _mem_subscriptions.get(teacher_phone, {
            "teacher_phone": teacher_phone,
            "tier": "free",
            "status": "active",
        })
    try:
        response = (
            supabase.table("subscriptions")
            .select("*")
            .eq("teacher_phone", teacher_phone)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Error getting subscription: {e}")
    return {"teacher_phone": teacher_phone, "tier": "free", "status": "active"}


def save_subscription(teacher_phone: str, tier: str, payment_ref: str = "",
                      school_phone: str = "") -> bool:
    """Create or update a subscription."""
    record = {
        "teacher_phone": teacher_phone,
        "tier": tier,
        "status": "active",
        "payment_ref": payment_ref,
        "school_phone": school_phone,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        _mem_subscriptions[teacher_phone] = record
        print(f"[local] Subscription {tier} for {teacher_phone}")
        return True
    try:
        supabase.table("subscriptions").upsert(
            record, on_conflict="teacher_phone"
        ).execute()
        return True
    except Exception as e:
        print(f"Error saving subscription: {e}")
        return False
