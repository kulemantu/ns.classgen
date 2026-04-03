"""Homework code storage for ClassGen.

Each generated lesson gets a short code that students use to access the quiz.
Codes expire after HOMEWORK_CODE_TTL_DAYS.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .client import supabase

# --- In-memory fallback store ---

_mem_homework: dict[str, dict] = {}

HOMEWORK_CODE_TTL_DAYS = 14


# --- Helpers ---


def _is_expired(created_at: str | None) -> bool:
    if not created_at:
        return False
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - created > timedelta(days=HOMEWORK_CODE_TTL_DAYS)
    except (ValueError, TypeError):
        return False


# --- Homework codes ---


def save_homework_code(code: str, thread_id: str, lesson_content: str,
                       quiz_questions: list, homework_block: str,
                       teacher_phone: str = "") -> bool:
    record = {
        "code": code,
        "thread_id": thread_id,
        "lesson_content": lesson_content,
        "quiz_questions": quiz_questions,
        "homework_block": homework_block,
    }
    if teacher_phone:
        record["teacher_phone"] = teacher_phone

    if not supabase:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
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
