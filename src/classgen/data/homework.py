"""Homework code storage for ClassGen.

Each generated lesson gets a short code that students use to access the quiz.
Codes expire after HOMEWORK_CODE_TTL_DAYS.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .client import supabase
from .teachers import get_teacher_by_phone


def build_homework_url(base_url: str, code: str, teacher_phone: str = "") -> str:
    """Build the canonical homework URL for ``code``.

    When ``teacher_phone`` resolves to a teacher with a slug, returns
    ``{base_url}/h/{slug}/{code}`` -- the attributed/branded URL.
    Otherwise returns the legacy ``{base_url}/h/{code}`` form. Both
    URL shapes are served by ``classgen.api.homework``; this helper just
    picks the prettier one when the teacher is known.
    """
    if teacher_phone:
        teacher = get_teacher_by_phone(teacher_phone)
        slug = teacher.get("slug") if teacher else ""
        if slug:
            return f"{base_url}/h/{slug}/{code}"
    return f"{base_url}/h/{code}"

# --- In-memory fallback store ---

_mem_homework: dict[str, dict] = {}

# Per-(teacher_phone, subject_code) counter mirroring the homework_subject_seq
# table. Migration 007 adds the Postgres-side equivalent; the dict keeps the
# in-memory test path behaving the same.
_mem_subject_seq: dict[tuple[str, str], int] = {}

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


def save_homework_code(
    code: str,
    thread_id: str,
    lesson_content: str,
    quiz_questions: list,
    homework_block: str,
    teacher_phone: str = "",
    lesson_json: dict | None = None,
) -> bool:
    record: dict = {
        "code": code,
        "thread_id": thread_id,
        "lesson_content": lesson_content,
        "quiz_questions": quiz_questions,
        "homework_block": homework_block,
    }
    if teacher_phone:
        record["teacher_phone"] = teacher_phone
    if lesson_json is not None:
        record["lesson_json"] = lesson_json

    if not supabase:
        if code in _mem_homework:
            # In-memory path mirrors the DB UNIQUE: caller must retry.
            return False
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        _mem_homework[code] = record
        print(f"[local] Saved homework code {code}")
        return True
    try:
        supabase.table("homework_codes").insert(record).execute()
        return True
    except Exception as e:
        # UNIQUE collisions are part of normal mnemonic-code operation now
        # (per-(teacher, subject) seq doesn't guarantee global freedom).
        # Return False so the caller can bump the seq and retry instead of
        # treating it as an unrecoverable error.
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


# --- Per-(teacher, subject) sequence counter ---


def next_homework_seq(teacher_phone: str, subject_code: str) -> int:
    """Atomically claim the next sequence number for (teacher, subject).

    Backed by the ``next_homework_seq`` Postgres function (migration 007)
    when a database is configured; falls through to an in-memory dict
    otherwise. Returns 1, 2, 3, ... in call order for a fresh pair.

    The atomic guarantee comes from Postgres' INSERT...ON CONFLICT; the
    in-memory path is single-process so plain increment is fine.
    """
    if not teacher_phone or not subject_code:
        return 0
    if not supabase:
        key = (teacher_phone, subject_code)
        seq = _mem_subject_seq.get(key, 0) + 1
        _mem_subject_seq[key] = seq
        return seq
    try:
        response = supabase.rpc(
            "next_homework_seq",
            {"p_teacher_phone": teacher_phone, "p_subject_code": subject_code},
        ).execute()
        # PostgREST returns the function's scalar return as response.data.
        # supabase-py wraps it; the shape is typically the raw int.
        data = response.data
        if isinstance(data, int):
            return data
        if isinstance(data, list) and data:
            # Some PostgREST configs wrap scalar returns in a single-row list.
            first = data[0]
            if isinstance(first, int):
                return first
            if isinstance(first, dict):
                # {"next_homework_seq": N}
                val = next(iter(first.values()), None)
                if isinstance(val, int):
                    return val
        if isinstance(data, dict):
            val = next(iter(data.values()), None)
            if isinstance(val, int):
                return val
        print(f"[seq] unexpected RPC shape: {data!r}")
        return 0
    except Exception as e:
        print(f"Error claiming homework seq: {e}")
        return 0


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
