"""Data access layer for ClassGen.

Handles all Supabase/Postgres operations with in-memory fallback for local dev.
Every table operation follows the pattern: save_X(), get_X(), list_X().
"""

import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- Client init ---

supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase: Client | None = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

# --- In-memory fallback stores ---

_mem_sessions: list[dict] = []
_mem_homework: dict[str, dict] = {}
_mem_submissions: dict[str, list] = {}
_mem_teachers: dict[str, dict] = {}  # keyed by phone number

HOMEWORK_CODE_TTL_DAYS = 14


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


# --- Homework codes ---

def _is_expired(created_at: str | None) -> bool:
    if not created_at:
        return False
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - created > timedelta(days=HOMEWORK_CODE_TTL_DAYS)
    except (ValueError, TypeError):
        return False


def save_homework_code(code: str, thread_id: str, lesson_content: str,
                       quiz_questions: list, homework_block: str,
                       teacher_phone: str = "") -> bool:
    record = {
        "code": code,
        "thread_id": thread_id,
        "lesson_content": lesson_content,
        "quiz_questions": quiz_questions,
        "homework_block": homework_block,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if teacher_phone:
        record["teacher_phone"] = teacher_phone

    if not supabase:
        _mem_homework[code] = record
        print(f"[local] Saved homework code {code}")
        return True
    try:
        supabase.table("homework_codes").insert(record).execute()
        return True
    except Exception as e:
        print(f"Error saving homework code: {e}")
        return False


def get_homework_code(code: str) -> dict | None:
    if not supabase:
        hw = _mem_homework.get(code)
        if hw and _is_expired(hw.get("created_at")):
            return None
        return hw
    try:
        response = supabase.table("homework_codes").select("*").eq("code", code).limit(1).execute()
        if not response.data:
            return None
        hw = response.data[0]
        if _is_expired(hw.get("created_at")):
            return None
        return hw
    except Exception as e:
        print(f"Error retrieving homework code: {e}")
        return None


def list_homework_codes_for_teacher(teacher_phone: str, limit: int = 10) -> list:
    """List recent homework codes created by a teacher."""
    if not supabase:
        codes = [hw for hw in _mem_homework.values() if hw.get("teacher_phone") == teacher_phone]
        return sorted(codes, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
    try:
        response = (
            supabase.table("homework_codes")
            .select("code, homework_block, created_at")
            .eq("teacher_phone", teacher_phone)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error listing homework codes: {e}")
        return []


# --- Quiz submissions ---

def save_quiz_submission(homework_code: str, student_name: str, student_class: str,
                         answers: list, score: int, total: int) -> bool:
    entry = {
        "homework_code": homework_code,
        "student_name": student_name,
        "student_class": student_class,
        "answers": answers,
        "score": score,
        "total": total,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
        _mem_submissions.setdefault(homework_code, []).append(entry)
        print(f"[local] Saved submission for {homework_code} by {student_name}")
        return True
    try:
        supabase.table("quiz_submissions").insert({
            "homework_code": homework_code,
            "student_name": student_name,
            "student_class": student_class,
            "answers": answers,
            "score": score,
            "total": total,
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving quiz submission: {e}")
        return False


def get_quiz_results(homework_code: str) -> list:
    if not supabase:
        return _mem_submissions.get(homework_code, [])
    try:
        response = (
            supabase.table("quiz_submissions")
            .select("*")
            .eq("homework_code", homework_code)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error retrieving quiz results: {e}")
        return []


# --- Teachers (V2.0) ---

def _make_slug(name: str) -> str:
    """Generate a URL-friendly slug from a teacher's name."""
    slug = name.lower().strip()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = "-".join(slug.split())
    return slug or "teacher"


def save_teacher(phone: str, name: str, school: str = "") -> dict:
    """Register or update a teacher. Returns the teacher record."""
    slug = _make_slug(name)
    record = {
        "phone": phone,
        "name": name,
        "slug": slug,
        "school": school,
        "classes": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
        existing = _mem_teachers.get(phone)
        if existing:
            existing["name"] = name
            existing["slug"] = slug
            if school:
                existing["school"] = school
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
