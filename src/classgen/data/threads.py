"""Active thread tracking for ClassGen session reset.

Maps phone numbers to their current active thread_id, allowing
conversation reset without losing the phone->thread association.
"""

from __future__ import annotations

# --- In-memory fallback store ---

_mem_active_threads: dict[str, str] = {}  # phone -> active thread_id


# --- Active Thread ---


def set_active_thread(phone: str, thread_id: str):
    """Set the active thread_id for a phone number (used by session reset)."""
    _mem_active_threads[phone] = thread_id


def get_active_thread(phone: str) -> str:
    """Get the active thread_id for a phone. Defaults to the phone number itself."""
    return _mem_active_threads.get(phone, phone)
