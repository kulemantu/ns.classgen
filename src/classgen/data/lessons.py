"""Lesson history and content cache for ClassGen.

Tracks which topics a teacher has covered and caches generated lesson content
for reuse.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .client import supabase

# --- In-memory fallback stores ---

_mem_lesson_history: list[dict] = []
_mem_content_cache: dict[str, str] = {}  # cache_key -> lesson content


# --- Lesson History ---


def log_lesson_generated(teacher_phone: str, subject: str, topic: str,
                         class_level: str, exam_board: str = "WAEC"):
    """Record that a teacher generated a lesson for a topic."""
    record = {
        "teacher_phone": teacher_phone,
        "subject": subject,
        "topic": topic,
        "class_level": class_level,
        "exam_board": exam_board,
    }
    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
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


# --- Content Cache ---


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
        }, on_conflict="cache_key").execute()
    except Exception as e:
        print(f"Error caching lesson: {e}")
