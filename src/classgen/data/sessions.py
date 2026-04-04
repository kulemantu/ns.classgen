"""Session history storage for ClassGen.

Stores conversation turns (role + content) keyed by thread_id.
"""

from __future__ import annotations

from .client import supabase

# --- In-memory fallback store ---

_mem_sessions: list[dict] = []


# --- Sessions ---


def log_session(thread_id: str, role: str, content: str):
    if not supabase:
        _mem_sessions.append({"thread_id": thread_id, "role": role, "content": content})
        print(f"[local] [{thread_id}] {role}: {content[:50]}...")
        return
    try:
        supabase.table("sessions").insert(
            {"thread_id": thread_id, "role": role, "content": content}
        ).execute()
    except Exception as e:
        print(f"Error logging to Supabase: {e}")


def get_session_history(thread_id: str, limit: int = 10) -> list:
    if not supabase:
        matches = [s for s in _mem_sessions if s["thread_id"] == thread_id]
        return matches[-limit:]
    try:
        response = (
            supabase.table("sessions")
            .select("*")
            .eq("thread_id", thread_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(response.data))
    except Exception as e:
        print(f"Error retrieving from Supabase: {e}")
        return []


def clear_session_history(thread_id: str) -> bool:
    """Delete all session records for a thread."""
    if not supabase:
        _mem_sessions[:] = [s for s in _mem_sessions if s["thread_id"] != thread_id]
        return True
    try:
        supabase.table("sessions").delete().eq("thread_id", thread_id).execute()
        return True
    except Exception as e:
        print(f"Error clearing session history: {e}")
        return False
