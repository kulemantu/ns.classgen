"""School registration and teacher association for ClassGen.

Handles school CRUD and listing teachers by school.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .client import supabase
from .teachers import _mem_teachers

# --- In-memory fallback store ---

_mem_schools: dict[str, dict] = {}


# --- Schools ---


def save_school(slug: str, name: str, admin_phone: str) -> dict:
    """Create or update a school."""
    record = {
        "slug": slug,
        "name": name,
        "admin_phone": admin_phone,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        _mem_schools[slug] = record
        print(f"[local] Created school {name}")
        return record
    try:
        supabase.table("schools").upsert(record, on_conflict="slug").execute()
        return record
    except Exception as e:
        print(f"Error saving school: {e}")
        return record


def get_school(slug: str) -> dict | None:
    if not supabase:
        return _mem_schools.get(slug)
    try:
        response = supabase.table("schools").select("*").eq("slug", slug).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting school: {e}")
        return None


def get_school_teachers(school_slug: str) -> list:
    """List teachers associated with a school."""
    if not supabase:
        return [t for t in _mem_teachers.values() if t.get("school_slug") == school_slug]
    try:
        response = supabase.table("teachers").select("*").eq("school_slug", school_slug).execute()
        return response.data
    except Exception as e:
        print(f"Error listing school teachers: {e}")
        return []
