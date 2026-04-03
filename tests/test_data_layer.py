"""Tests for nuanced behavior in the classgen data layer.

All tests use the in-memory fallback (supabase=None). No external
services or mocking of Supabase is needed -- we patch each module's
``supabase`` binding to None and operate directly against the
in-memory dicts/lists.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from classgen.data.homework import (
    _mem_homework,
    get_homework_code,
    save_homework_code,
)
from classgen.data.lessons import (
    _mem_content_cache,
    _mem_lesson_history,
    cache_lesson,
    get_cached_lesson,
)
from classgen.data.sessions import (
    _mem_sessions,
    get_session_history,
    log_session,
)
from classgen.data.subscriptions import (
    _mem_usage,
    get_weekly_usage,
    log_usage,
)
from classgen.data.teachers import (
    _mem_teachers,
    add_teacher_class,
    get_teacher_by_phone,
    save_teacher,
)

# -- Fixtures to reset in-memory state between tests --


@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset all in-memory stores before and after each test."""
    _mem_homework.clear()
    _mem_teachers.clear()
    _mem_sessions.clear()
    _mem_content_cache.clear()
    _mem_lesson_history.clear()
    _mem_usage.clear()
    yield
    _mem_homework.clear()
    _mem_teachers.clear()
    _mem_sessions.clear()
    _mem_content_cache.clear()
    _mem_lesson_history.clear()
    _mem_usage.clear()


# -------------------------------------------------------------------
# Homework TTL expiry
# -------------------------------------------------------------------


class TestHomeworkTTLExpiry:
    """Codes older than 14 days must be treated as expired."""

    @patch("classgen.data.homework.supabase", None)
    def test_expired_code_returns_none(self):
        save_homework_code(
            code="EXP15",
            thread_id="t1",
            lesson_content="content",
            quiz_questions=[],
            homework_block="block",
        )
        fifteen_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=15)
        ).isoformat()
        _mem_homework["EXP15"]["created_at"] = fifteen_days_ago

        assert get_homework_code("EXP15") is None

    @patch("classgen.data.homework.supabase", None)
    def test_recent_code_returns_record(self):
        save_homework_code(
            code="REC13",
            thread_id="t2",
            lesson_content="content",
            quiz_questions=[],
            homework_block="block",
        )
        thirteen_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=13)
        ).isoformat()
        _mem_homework["REC13"]["created_at"] = thirteen_days_ago

        result = get_homework_code("REC13")
        assert result is not None
        assert result["code"] == "REC13"

    @patch("classgen.data.homework.supabase", None)
    def test_boundary_just_under_14_days_not_expired(self):
        """A code created 13 days 23 hours ago is still valid."""
        save_homework_code(
            code="EDGE",
            thread_id="t3",
            lesson_content="content",
            quiz_questions=[],
            homework_block="block",
        )
        just_under = (
            datetime.now(timezone.utc)
            - timedelta(days=13, hours=23)
        ).isoformat()
        _mem_homework["EDGE"]["created_at"] = just_under

        result = get_homework_code("EDGE")
        assert result is not None


# -------------------------------------------------------------------
# Teacher slug deduplication
# -------------------------------------------------------------------


class TestTeacherSlugDeduplication:
    """Two teachers with the same name get distinct slugs."""

    @patch("classgen.data.teachers.supabase", None)
    def test_different_slugs_for_same_name(self):
        t1 = save_teacher(
            phone="+2341111111111",
            name="Adaeze Okafor",
        )
        t2 = save_teacher(
            phone="+2342222222222",
            name="Adaeze Okafor",
        )
        assert t1["slug"] != t2["slug"]
        # First teacher gets the clean slug
        assert t1["slug"] == "adaeze-okafor"
        # Second gets a suffix from the phone number
        assert t2["slug"].startswith("adaeze-okafor-")

    @patch("classgen.data.teachers.supabase", None)
    def test_same_phone_keeps_same_slug(self):
        """Re-registering with the same phone should not collide
        with itself."""
        t1 = save_teacher(
            phone="+2341111111111",
            name="Adaeze Okafor",
        )
        t2 = save_teacher(
            phone="+2341111111111",
            name="Adaeze Okafor",
        )
        assert t1["slug"] == t2["slug"]


# -------------------------------------------------------------------
# Teacher upsert preserves data
# -------------------------------------------------------------------


class TestTeacherUpsertPreservesData:
    """Re-registering updates name but keeps classes."""

    @patch("classgen.data.teachers.supabase", None)
    def test_classes_preserved_after_reregister(self):
        save_teacher(
            phone="+2349000000001",
            name="Bola Ahmed",
        )
        add_teacher_class("+2349000000001", "SS2 Biology")
        add_teacher_class("+2349000000001", "SS1 Chemistry")

        # Re-register with a new name
        updated = save_teacher(
            phone="+2349000000001",
            name="Bola Tinubu",
        )

        assert updated["name"] == "Bola Tinubu"
        assert "SS2 Biology" in updated["classes"]
        assert "SS1 Chemistry" in updated["classes"]

    @patch("classgen.data.teachers.supabase", None)
    def test_name_actually_changes(self):
        save_teacher(
            phone="+2349000000002", name="Old Name",
        )
        save_teacher(
            phone="+2349000000002", name="New Name",
        )

        teacher = get_teacher_by_phone("+2349000000002")
        assert teacher is not None
        assert teacher["name"] == "New Name"


# -------------------------------------------------------------------
# Session history ordering
# -------------------------------------------------------------------


class TestSessionHistoryOrdering:
    """History returns in chronological (oldest-first) order."""

    @patch("classgen.data.sessions.supabase", None)
    def test_chronological_order(self):
        log_session("thread-A", "user", "first message")
        log_session("thread-A", "assistant", "second message")
        log_session("thread-A", "user", "third message")

        history = get_session_history("thread-A")
        assert len(history) == 3
        assert history[0]["content"] == "first message"
        assert history[1]["content"] == "second message"
        assert history[2]["content"] == "third message"

    @patch("classgen.data.sessions.supabase", None)
    def test_limit_keeps_most_recent(self):
        for i in range(5):
            log_session("thread-B", "user", f"msg-{i}")

        history = get_session_history("thread-B", limit=3)
        assert len(history) == 3
        # Last three, still in chronological order
        assert history[0]["content"] == "msg-2"
        assert history[1]["content"] == "msg-3"
        assert history[2]["content"] == "msg-4"

    @patch("classgen.data.sessions.supabase", None)
    def test_different_threads_isolated(self):
        log_session("thread-X", "user", "X message")
        log_session("thread-Y", "user", "Y message")

        x = get_session_history("thread-X")
        y = get_session_history("thread-Y")
        assert len(x) == 1
        assert len(y) == 1
        assert x[0]["content"] == "X message"


# -------------------------------------------------------------------
# Lesson cache exact match
# -------------------------------------------------------------------


class TestLessonCacheExactMatch:
    """Cache hits require exact (subject, topic, class) tuple."""

    @patch("classgen.data.lessons.supabase", None)
    def test_cache_hit(self):
        cache_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS2",
            content="Lesson about photosynthesis.",
        )
        result = get_cached_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS2",
        )
        assert result == "Lesson about photosynthesis."

    @patch("classgen.data.lessons.supabase", None)
    def test_cache_miss_different_subject(self):
        cache_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS2",
            content="Biology lesson.",
        )
        result = get_cached_lesson(
            subject="Chemistry",
            topic="Photosynthesis",
            class_level="SS2",
        )
        assert result is None

    @patch("classgen.data.lessons.supabase", None)
    def test_cache_miss_different_class_level(self):
        cache_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS2",
            content="SS2 lesson.",
        )
        result = get_cached_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS1",
        )
        assert result is None

    @patch("classgen.data.lessons.supabase", None)
    def test_cache_key_is_case_insensitive(self):
        cache_lesson(
            subject="Biology",
            topic="Photosynthesis",
            class_level="SS2",
            content="Lesson content.",
        )
        result = get_cached_lesson(
            subject="biology",
            topic="photosynthesis",
            class_level="ss2",
        )
        assert result == "Lesson content."


# -------------------------------------------------------------------
# Weekly usage reset at Monday boundary
# -------------------------------------------------------------------


class TestWeeklyUsageReset:
    """Usage counter resets every Monday at 00:00 UTC."""

    @patch("classgen.data.subscriptions.supabase", None)
    def test_counts_current_week_only(self):
        phone = "+2340000000001"
        log_usage(phone, action="lesson")
        log_usage(phone, action="lesson")

        assert get_weekly_usage(phone) == 2

    @patch("classgen.data.subscriptions.supabase", None)
    def test_excludes_last_week_entries(self):
        phone = "+2340000000002"
        log_usage(phone, action="lesson")

        # Back-date the entry to last week
        now = datetime.now(timezone.utc)
        last_week = now - timedelta(days=8)
        _mem_usage[phone][0]["created_at"] = (
            last_week.isoformat()
        )

        assert get_weekly_usage(phone) == 0

    @patch("classgen.data.subscriptions.supabase", None)
    def test_ignores_non_lesson_actions(self):
        phone = "+2340000000003"
        log_usage(phone, action="lesson")
        log_usage(phone, action="quiz")

        assert get_weekly_usage(phone) == 1

    @patch("classgen.data.subscriptions.supabase", None)
    def test_monday_boundary(self):
        """An entry from last Sunday should not count, but one
        from this Monday should."""
        phone = "+2340000000004"

        now = datetime.now(timezone.utc)
        # Monday of this week at 00:00
        monday = (
            now.replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            - timedelta(days=now.weekday())
        )
        sunday_before = monday - timedelta(hours=1)

        # Create two entries manually
        _mem_usage[phone] = [
            {
                "teacher_phone": phone,
                "action": "lesson",
                "created_at": sunday_before.isoformat(),
            },
            {
                "teacher_phone": phone,
                "action": "lesson",
                "created_at": monday.isoformat(),
            },
        ]

        # Only the Monday entry counts
        assert get_weekly_usage(phone) == 1
