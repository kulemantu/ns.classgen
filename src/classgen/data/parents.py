"""Parent subscription management for ClassGen.

Parents subscribe to weekly digests about their child's progress in a
teacher's class.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .client import supabase

# --- In-memory fallback store ---

_mem_parent_subs: dict[str, dict] = {}


# --- Parent Subscriptions ---


def save_parent_subscription(
    parent_phone: str, teacher_phone: str, student_name: str, student_class: str
) -> bool:
    """Subscribe a parent to weekly digests for a teacher's class."""
    key = f"{parent_phone}:{teacher_phone}:{student_class}"
    record = {
        "parent_phone": parent_phone,
        "teacher_phone": teacher_phone,
        "student_name": student_name,
        "student_class": student_class,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        _mem_parent_subs[key] = record
        print(f"[local] Parent {parent_phone} subscribed to {student_class}")
        return True
    try:
        supabase.table("parent_subscriptions").upsert(
            record, on_conflict="parent_phone,teacher_phone,student_class"
        ).execute()
        return True
    except Exception as e:
        print(f"Error saving parent subscription: {e}")
        return False


def list_parent_subscriptions(teacher_phone: str) -> list:
    """List all parent subscriptions for a teacher."""
    if not supabase:
        return [s for s in _mem_parent_subs.values() if s.get("teacher_phone") == teacher_phone]
    try:
        response = (
            supabase.table("parent_subscriptions")
            .select("*")
            .eq("teacher_phone", teacher_phone)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error listing parent subscriptions: {e}")
        return []


def unsubscribe_parent(parent_phone: str, teacher_phone: str, student_class: str) -> bool:
    """Remove a parent subscription."""
    key = f"{parent_phone}:{teacher_phone}:{student_class}"
    if not supabase:
        return _mem_parent_subs.pop(key, None) is not None
    try:
        supabase.table("parent_subscriptions").delete().match(
            {
                "parent_phone": parent_phone,
                "teacher_phone": teacher_phone,
                "student_class": student_class,
            }
        ).execute()
        return True
    except Exception as e:
        print(f"Error unsubscribing parent: {e}")
        return False
