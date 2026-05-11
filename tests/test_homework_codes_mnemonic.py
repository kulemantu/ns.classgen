"""Mnemonic homework codes -- generator, counter, helper, routes.

Covers the move from random 6-char codes (ZQXJ73) to per-(teacher, subject)
mnemonic codes (BIOL01, MATH02). Tests exercise the in-memory fallback path
(no Supabase) since the data layer transparently switches based on the
``supabase`` global.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.content.subjects import derive_subject_prefix
from classgen.data.homework import (
    _mem_homework,
    _mem_subject_seq,
    build_homework_url,
    next_homework_seq,
    save_homework_code,
)
from classgen.data.teachers import _mem_teachers, save_teacher
from classgen.services.llm import generate_homework_code

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset in-memory stores before/after every test."""
    _mem_homework.clear()
    _mem_subject_seq.clear()
    _mem_teachers.clear()
    yield
    _mem_homework.clear()
    _mem_subject_seq.clear()
    _mem_teachers.clear()


# ---------------------------------------------------------------------------
# Subject prefix derivation
# ---------------------------------------------------------------------------


class TestSubjectPrefix:
    def test_known_subjects(self):
        """Curriculum-core subjects map to predictable 4-letter prefixes."""
        assert derive_subject_prefix("Biology") == "BIOL"
        assert derive_subject_prefix("Mathematics") == "MATH"
        assert derive_subject_prefix("Physics") == "PHYS"
        assert derive_subject_prefix("Chemistry") == "CHEM"
        assert derive_subject_prefix("English") == "ENGL"
        assert derive_subject_prefix("History") == "HIST"

    def test_aliases_normalize(self):
        """Common shortenings collapse to the same canonical prefix."""
        assert derive_subject_prefix("Bio") == "BIOL"
        assert derive_subject_prefix("Maths") == "MATH"
        assert derive_subject_prefix("Math") == "MATH"
        assert derive_subject_prefix("Geo") == "GEOG"

    def test_multi_token_picks_leading_qualifier(self):
        """`further maths` -> FMTH, not MATH (qualifier wins)."""
        assert derive_subject_prefix("further maths") == "FMTH"

    def test_topic_string_finds_subject(self):
        """Subjects appear inside the user's lesson topic string."""
        assert derive_subject_prefix("SS2 Biology: Photosynthesis") == "BIOL"
        assert derive_subject_prefix("JSS1 mathematics -- algebra") == "MATH"

    def test_unknown_returns_empty(self):
        """Off-curriculum or empty -> empty string (caller falls back to random)."""
        assert derive_subject_prefix("") == ""
        assert derive_subject_prefix("Astrophysics 7000") == ""
        assert derive_subject_prefix("Quidditch") == ""

    def test_case_insensitive(self):
        assert derive_subject_prefix("BIOLOGY") == "BIOL"
        assert derive_subject_prefix("bIoLoGy") == "BIOL"


# ---------------------------------------------------------------------------
# next_homework_seq -- per-(teacher, subject) counter
# ---------------------------------------------------------------------------


class TestSeqCounter:
    def test_first_call_returns_one(self):
        assert next_homework_seq("+234555", "BIOL") == 1

    def test_increments_per_teacher_subject_pair(self):
        assert next_homework_seq("+234555", "BIOL") == 1
        assert next_homework_seq("+234555", "BIOL") == 2
        assert next_homework_seq("+234555", "BIOL") == 3

    def test_subjects_isolated_within_teacher(self):
        """BIOL and MATH counters don't share state."""
        assert next_homework_seq("+234555", "BIOL") == 1
        assert next_homework_seq("+234555", "MATH") == 1
        assert next_homework_seq("+234555", "BIOL") == 2

    def test_teachers_isolated_per_subject(self):
        """Alice's BIOL and Bob's BIOL count independently."""
        assert next_homework_seq("+234111", "BIOL") == 1
        assert next_homework_seq("+234222", "BIOL") == 1
        assert next_homework_seq("+234111", "BIOL") == 2

    def test_missing_args_return_zero(self):
        """Empty teacher or subject is a signal to skip the counter."""
        assert next_homework_seq("", "BIOL") == 0
        assert next_homework_seq("+234555", "") == 0


# ---------------------------------------------------------------------------
# generate_homework_code -- the main entry point
# ---------------------------------------------------------------------------


class TestGenerateHomeworkCode:
    def test_random_when_no_args(self):
        """Legacy call signature still produces a random 6-char code."""
        code = generate_homework_code()
        assert len(code) == 6
        assert code[:4].isalpha() and code[:4].isupper()
        assert code[4:].isdigit()

    def test_mnemonic_when_teacher_and_subject_known(self):
        """Known subject + teacher -> prefix + 2-digit suffix."""
        code = generate_homework_code("+234555", "Biology")
        assert code == "BIOL01"
        code = generate_homework_code("+234555", "Biology")
        assert code == "BIOL02"

    def test_random_when_subject_unknown(self):
        """Off-curriculum subject falls back to random rather than coining a prefix."""
        code = generate_homework_code("+234555", "Quidditch")
        assert len(code) == 6
        # Not a deterministic prefix from the map.
        assert not code.startswith("QUID")

    def test_random_when_teacher_missing(self):
        """No teacher_phone -> random (counter is teacher-scoped)."""
        code = generate_homework_code("", "Biology")
        assert len(code) == 6
        # Counter wasn't consulted, so no BIOL prefix promised.
        # (It could still randomly be BIOL by coincidence, but extremely rare.)

    def test_counter_falls_back_to_random_past_99(self):
        """Once a (teacher, subject) pair hits seq 100, generator drops to random."""
        from classgen.data.homework import _mem_subject_seq

        _mem_subject_seq[("+234555", "BIOL")] = 99  # next call yields 100
        code = generate_homework_code("+234555", "Biology")
        # Either format is acceptable -- mnemonic requires seq <= 99.
        # Confirm we DIDN'T emit "BIOL100" (would break the 6-char shape).
        assert len(code) == 6


# ---------------------------------------------------------------------------
# save_homework_code -- collision behavior
# ---------------------------------------------------------------------------


class TestSaveCollision:
    def test_first_save_succeeds(self):
        assert save_homework_code("MATH01", "thread1", "lesson", [], "") is True

    def test_second_save_same_code_returns_false(self):
        """Mnemonic codes share a small namespace; the in-memory store mirrors
        the DB UNIQUE so callers can retry."""
        assert save_homework_code("MATH01", "thread1", "lesson", [], "") is True
        assert save_homework_code("MATH01", "thread2", "other lesson", [], "") is False


# ---------------------------------------------------------------------------
# build_homework_url -- chooses /h/{slug}/{code} vs /h/{code}
# ---------------------------------------------------------------------------


class TestBuildHomeworkUrl:
    def test_teacher_known_uses_slug(self):
        save_teacher("+234555", "Mrs Okafor")
        url = build_homework_url("https://x.example", "BIOL01", "+234555")
        # Slug is derived from name -- check the shape rather than the exact slug.
        assert url.startswith("https://x.example/h/")
        assert url.endswith("/BIOL01")
        # Two path segments after /h/
        assert url.count("/h/") == 1 and url.split("/h/")[1].count("/") == 1

    def test_no_teacher_falls_back_to_legacy(self):
        url = build_homework_url("https://x.example", "BIOL01", "")
        assert url == "https://x.example/h/BIOL01"

    def test_unknown_phone_falls_back_to_legacy(self):
        url = build_homework_url("https://x.example", "BIOL01", "+999notreal")
        assert url == "https://x.example/h/BIOL01"


# ---------------------------------------------------------------------------
# Teacher-scoped HTTP routes
# ---------------------------------------------------------------------------


class TestScopedRoutes:
    def _seed(self, *, with_teacher: bool = True) -> tuple[str, str, str]:
        """Save a teacher + homework_code, return (phone, slug, code)."""
        phone = "+234555000"
        save_teacher(phone, "Mr Adeyemi")
        slug = _mem_teachers[phone]["slug"]
        save_homework_code(
            "BIOL01",
            "thread-x",
            "lesson content",
            [],
            "homework block",
            teacher_phone=phone if with_teacher else "",
        )
        return phone, slug, "BIOL01"

    def test_legacy_route_still_works(self):
        """``/h/{code}`` continues to serve regardless of slug awareness."""
        self._seed()
        response = client.get("/h/BIOL01")
        assert response.status_code == 200

    def test_scoped_route_serves_with_correct_slug(self):
        _phone, slug, code = self._seed()
        response = client.get(f"/h/{slug}/{code}")
        assert response.status_code == 200

    def test_scoped_route_404s_with_wrong_slug(self):
        """Wrong slug must not surface another teacher's code."""
        self._seed()
        response = client.get("/h/some-other-teacher/BIOL01")
        assert response.status_code == 404

    def test_scoped_route_404s_when_code_has_no_teacher(self):
        """Pre-mnemonic codes (no teacher_phone) aren't reachable via scoped URL."""
        _phone, slug, code = self._seed(with_teacher=False)
        response = client.get(f"/h/{slug}/{code}")
        assert response.status_code == 404

    def test_scoped_api_data_matches_legacy(self):
        _phone, slug, code = self._seed()
        legacy = client.get(f"/api/h/{code}").json()
        scoped = client.get(f"/api/h/{slug}/{code}").json()
        assert legacy == scoped
