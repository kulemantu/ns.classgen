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
_mem_lesson_history: list[dict] = []
_mem_content_cache: dict[str, str] = {}  # cache_key -> lesson content

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


# --- Student Progress (V2.1) ---

def get_student_progress(student_name: str, student_class: str) -> list:
    """Get all quiz submissions for a student across all homework codes."""
    if not supabase:
        results = []
        for subs in _mem_submissions.values():
            for s in subs:
                if s.get("student_name") == student_name and s.get("student_class") == student_class:
                    results.append(s)
        return sorted(results, key=lambda x: x.get("created_at") or "", reverse=True)
    try:
        response = (
            supabase.table("quiz_submissions")
            .select("*")
            .eq("student_name", student_name)
            .eq("student_class", student_class)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error retrieving student progress: {e}")
        return []


def get_class_leaderboard(homework_code: str, limit: int = 10) -> list:
    """Get top-scoring students for a homework code."""
    submissions = get_quiz_results(homework_code)
    # Sort by score descending, then by name for tiebreaker
    ranked = sorted(submissions, key=lambda s: (-s.get("score", 0), s.get("student_name", "")))
    return ranked[:limit]


# --- Parent Subscriptions (V2.1) ---

_mem_parent_subs: dict[str, dict] = {}


def save_parent_subscription(parent_phone: str, teacher_phone: str,
                             student_name: str, student_class: str) -> bool:
    """Subscribe a parent to weekly digests for a teacher's class."""
    key = f"{parent_phone}:{teacher_phone}:{student_class}"
    record = {
        "parent_phone": parent_phone,
        "teacher_phone": teacher_phone,
        "student_name": student_name,
        "student_class": student_class,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
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
        supabase.table("parent_subscriptions").delete().match({
            "parent_phone": parent_phone,
            "teacher_phone": teacher_phone,
            "student_class": student_class,
        }).execute()
        return True
    except Exception as e:
        print(f"Error unsubscribing parent: {e}")
        return False


# --- Lesson History (V3.0a) ---

def log_lesson_generated(teacher_phone: str, subject: str, topic: str,
                         class_level: str, exam_board: str = "WAEC"):
    """Record that a teacher generated a lesson for a topic."""
    record = {
        "teacher_phone": teacher_phone,
        "subject": subject,
        "topic": topic,
        "class_level": class_level,
        "exam_board": exam_board,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
        _mem_lesson_history.append(record)
        return
    try:
        supabase.table("lesson_history").insert(record).execute()
    except Exception as e:
        print(f"Error logging lesson history: {e}")


def get_covered_topics(teacher_phone: str, class_str: str) -> list[str]:
    """Get topics a teacher has already generated for a class (e.g. 'SS2 Biology')."""
    parts = class_str.strip().split(maxsplit=1)
    if len(parts) < 2:
        return []
    class_level, subject = parts[0].upper(), parts[1].strip()

    if not supabase:
        return [
            h["topic"] for h in _mem_lesson_history
            if h.get("teacher_phone") == teacher_phone
            and h.get("class_level") == class_level
            and h.get("subject", "").lower() == subject.lower()
        ]
    try:
        response = (
            supabase.table("lesson_history")
            .select("topic")
            .eq("teacher_phone", teacher_phone)
            .eq("class_level", class_level)
            .ilike("subject", subject)
            .execute()
        )
        return [r["topic"] for r in response.data]
    except Exception as e:
        print(f"Error getting covered topics: {e}")
        return []


# --- Content Cache (V3.0a) ---

def _cache_key(subject: str, topic: str, class_level: str, exam_board: str) -> str:
    return f"{exam_board}:{subject}:{class_level}:{topic}".lower()


def get_cached_lesson(subject: str, topic: str, class_level: str,
                      exam_board: str = "WAEC") -> str | None:
    """Check if a lesson for this exact tuple has been generated before."""
    key = _cache_key(subject, topic, class_level, exam_board)
    if not supabase:
        return _mem_content_cache.get(key)
    try:
        response = (
            supabase.table("lesson_cache")
            .select("content")
            .eq("cache_key", key)
            .limit(1)
            .execute()
        )
        return response.data[0]["content"] if response.data else None
    except Exception as e:
        print(f"Error checking content cache: {e}")
        return None


def cache_lesson(subject: str, topic: str, class_level: str,
                 content: str, exam_board: str = "WAEC"):
    """Cache a generated lesson for reuse."""
    key = _cache_key(subject, topic, class_level, exam_board)
    if not supabase:
        _mem_content_cache[key] = content
        return
    try:
        supabase.table("lesson_cache").upsert({
            "cache_key": key,
            "subject": subject,
            "topic": topic,
            "class_level": class_level,
            "exam_board": exam_board,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="cache_key").execute()
    except Exception as e:
        print(f"Error caching lesson: {e}")


# --- Schools (V3.0c) ---

_mem_schools: dict[str, dict] = {}


def save_school(slug: str, name: str, admin_phone: str) -> dict:
    """Create or update a school."""
    record = {
        "slug": slug,
        "name": name,
        "admin_phone": admin_phone,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
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
        response = (
            supabase.table("teachers")
            .select("*")
            .eq("school_slug", school_slug)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error listing school teachers: {e}")
        return []
