"""Push subscription data access for ClassGen.

CRUD operations for Web Push notification subscriptions with in-memory fallback.
"""

from __future__ import annotations

from classgen.data.client import supabase

# --- In-memory fallback store ---

_mem_subscriptions: dict[str, list[dict]] = {}


# --- Push subscriptions ---


def save_push_subscription(teacher_id: str, subscription: dict) -> bool:
    """Save a push subscription for a teacher (thread_id or phone)."""
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
        supabase.table("push_subscriptions").upsert(
            {
                "teacher_id": teacher_id,
                "endpoint": endpoint,
                "subscription": subscription,
            },
            on_conflict="endpoint",
        ).execute()
        return True
    except Exception as e:
        print(f"Error saving push subscription: {e}")
        return False


def get_push_subscriptions(teacher_id: str) -> list[dict]:
    """Get all push subscriptions for a teacher."""
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
    if not supabase:
        for subs in _mem_subscriptions.values():
            subs[:] = [s for s in subs if s.get("endpoint") != endpoint]
        return
    try:
        supabase.table("push_subscriptions").delete().eq("endpoint", endpoint).execute()
    except Exception as e:
        print(f"Error removing push subscription: {e}")
