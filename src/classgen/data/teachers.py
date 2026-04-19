"""Teacher registration and profile management for ClassGen.

Handles teacher CRUD, slug generation, and class list management.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .client import supabase

# --- In-memory fallback store ---

_mem_teachers: dict[str, dict] = {}  # keyed by phone number


# --- Slug helpers ---


def _make_slug(name: str) -> str:
    """Generate a URL-friendly slug from a teacher's name."""
    slug = name.lower().strip()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = "-".join(slug.split())
    return slug or "teacher"


def _unique_slug(slug: str, phone: str) -> str:
    """Ensure slug is unique by appending digits if needed."""
    existing = get_teacher_by_slug(slug)
    if not existing or existing.get("phone") == phone:
        return slug
    # Collision — append last 4 digits of phone
    suffix = phone[-4:].replace("+", "")
    return f"{slug}-{suffix}"


# --- Teachers ---


def save_teacher(
    phone: str, name: str, school: str = "", school_slug: str = "", country: str = ""
) -> dict:
    """Register or update a teacher. Returns the teacher record."""
    slug = _unique_slug(_make_slug(name), phone)
    record = {
        "phone": phone,
        "name": name,
        "slug": slug,
        "school": school,
        "school_slug": school_slug,
        "classes": [],
        "country": country,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        existing = _mem_teachers.get(phone)
        if existing:
            existing["name"] = name
            existing["slug"] = slug
            if school:
                existing["school"] = school
            if country:
                existing["country"] = country
            return existing
        _mem_teachers[phone] = record
        print(f"[local] Registered teacher {name} ({phone})")
        return record
    try:
        # Upsert by phone
        supabase.table("teachers").upsert(record, on_conflict="phone").execute()
        return record
    except Exception as e:
        print(f"Error saving teacher: {e}")
        return record


def get_teacher_by_phone(phone: str) -> dict | None:
    if not supabase:
        return _mem_teachers.get(phone)
    try:
        response = supabase.table("teachers").select("*").eq("phone", phone).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error retrieving teacher: {e}")
        return None


def get_teacher_by_slug(slug: str) -> dict | None:
    if not supabase:
        for t in _mem_teachers.values():
            if t.get("slug") == slug:
                return t
        return None
    try:
        response = supabase.table("teachers").select("*").eq("slug", slug).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error retrieving teacher by slug: {e}")
        return None


def add_teacher_class(phone: str, class_name: str) -> bool:
    """Add a class (e.g. 'SS2 Biology') to a teacher's class list."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return False
    classes = teacher.get("classes", [])
    if class_name not in classes:
        classes.append(class_name)
    if not supabase:
        teacher["classes"] = classes
        return True
    try:
        supabase.table("teachers").update({"classes": classes}).eq("phone", phone).execute()
        return True
    except Exception as e:
        print(f"Error adding class: {e}")
        return False


def remove_teacher_class(phone: str, class_name: str) -> bool:
    """Remove a class from a teacher's class list."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return False
    classes = [c for c in teacher.get("classes", []) if c != class_name]
    if not supabase:
        teacher["classes"] = classes
        return True
    try:
        supabase.table("teachers").update({"classes": classes}).eq("phone", phone).execute()
        return True
    except Exception as e:
        print(f"Error removing class: {e}")
        return False


def update_teacher_name(phone: str, new_name: str) -> dict | None:
    """Update a teacher's name and regenerate slug."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return None
    new_slug = _unique_slug(_make_slug(new_name), phone)
    if not supabase:
        teacher["name"] = new_name
        teacher["slug"] = new_slug
        return teacher
    try:
        supabase.table("teachers").update(
            {
                "name": new_name,
                "slug": new_slug,
            }
        ).eq("phone", phone).execute()
        teacher["name"] = new_name
        teacher["slug"] = new_slug
        return teacher
    except Exception as e:
        print(f"Error updating teacher name: {e}")
        return None


def update_teacher_country(phone: str, country: str) -> dict | None:
    """Update a teacher's country."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return None
    if not supabase:
        teacher["country"] = country
        return teacher
    try:
        supabase.table("teachers").update({"country": country}).eq("phone", phone).execute()
        teacher["country"] = country
        return teacher
    except Exception as e:
        print(f"Error updating teacher country: {e}")
        return None


def get_teacher_lesson_stats(teacher_phone: str) -> dict:
    """Count lessons generated: total, this week, this month.

    NOTE: This queries the homework_codes table, which lives in the homework
    module.  We import the in-memory store lazily to avoid circular imports
    while keeping the function on the teacher namespace where callers expect it.
    """
    from datetime import timedelta

    from .homework import _mem_homework

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if not supabase:
        codes = [hw for hw in _mem_homework.values() if hw.get("teacher_phone") == teacher_phone]
        total = len(codes)
        this_week = sum(1 for hw in codes if hw.get("created_at", "") >= week_start.isoformat())
        this_month = sum(1 for hw in codes if hw.get("created_at", "") >= month_start.isoformat())
        return {"total": total, "this_week": this_week, "this_month": this_month}
    try:
        resp = (
            supabase.table("homework_codes")
            .select("created_at")
            .eq("teacher_phone", teacher_phone)
            .execute()
        )
        all_codes = resp.data
        total = len(all_codes)
        this_week = sum(1 for hw in all_codes if hw.get("created_at", "") >= week_start.isoformat())
        this_month = sum(
            1 for hw in all_codes if hw.get("created_at", "") >= month_start.isoformat()
        )
        return {"total": total, "this_week": this_week, "this_month": this_month}
    except Exception as e:
        print(f"Error getting teacher stats: {e}")
        return {"total": 0, "this_week": 0, "this_month": 0}


# --- Onboarding ---


def is_onboarded(phone: str) -> bool:
    """Check if a user has accepted the onboarding terms."""
    if not supabase:
        teacher = _mem_teachers.get(phone)
        return bool(teacher and teacher.get("onboarded_at"))
    try:
        resp = (
            supabase.table("teachers").select("onboarded_at").eq("phone", phone).limit(1).execute()
        )
        if resp.data:
            return resp.data[0].get("onboarded_at") is not None
        return False
    except Exception as e:
        print(f"Error checking onboarding: {e}")
        return False


def mark_onboarded(phone: str) -> bool:
    """Record that a user accepted the onboarding terms."""
    now = datetime.now(timezone.utc).isoformat()
    if not supabase:
        teacher = _mem_teachers.get(phone)
        if teacher:
            teacher["onboarded_at"] = now
        return True
    try:
        supabase.table("teachers").update({"onboarded_at": now}).eq("phone", phone).execute()
        return True
    except Exception as e:
        print(f"Error marking onboarded: {e}")
        return False
