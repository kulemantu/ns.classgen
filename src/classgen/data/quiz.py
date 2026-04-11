"""Quiz submission storage and analytics for ClassGen.

Stores student answers, scores, and provides aggregation for progress
tracking and leaderboards.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .client import supabase

# --- In-memory fallback store ---

_mem_submissions: dict[str, list] = {}


# --- Quiz submissions ---


def save_quiz_submission(
    homework_code: str, student_name: str, student_class: str, answers: list, score: int, total: int
) -> bool:
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
        supabase.table("quiz_submissions").insert(
            {
                "homework_code": homework_code,
                "student_name": student_name,
                "student_class": student_class,
                "answers": answers,
                "score": score,
                "total": total,
            }
        ).execute()
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


def get_student_progress(student_name: str, student_class: str) -> list:
    """Get all quiz submissions for a student across all homework codes."""
    if not supabase:
        results = []
        for subs in _mem_submissions.values():
            for s in subs:
                if (
                    s.get("student_name") == student_name
                    and s.get("student_class") == student_class
                ):
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


def count_quiz_submissions_for_codes(codes: list[str]) -> int:
    """Count total quiz submissions across a list of homework codes."""
    if not supabase:
        return sum(len(_mem_submissions.get(c, [])) for c in codes)
    try:
        total = 0
        # Query in batches to avoid overly long filters
        for c in codes:
            resp = (
                supabase.table("quiz_submissions")
                .select("homework_code", count="exact")
                .eq("homework_code", c)
                .execute()
            )
            total += resp.count if resp.count else len(resp.data)
        return total
    except Exception as e:
        print(f"Error counting quiz submissions: {e}")
        return 0


def get_class_leaderboard(homework_code: str, limit: int = 10) -> list:
    """Get top-scoring students for a homework code."""
    submissions = get_quiz_results(homework_code)
    # Sort by score descending, then by name for tiebreaker
    ranked = sorted(submissions, key=lambda s: (-s.get("score", 0), s.get("student_name", "")))
    return ranked[:limit]
