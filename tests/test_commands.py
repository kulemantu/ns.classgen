"""Tests for the WhatsApp command router and all handler functions.

Exercises every command path through handle_command() to verify correct
dispatch, reply content, session actions, and fall-through to LLM (None).

All tests use the in-memory fallback data stores (no Supabase) so they
run without any external services.
"""

from __future__ import annotations

from classgen.commands.router import handle_command
from classgen.data.teachers import _mem_teachers, save_teacher

PHONE = "+23412345678"
BASE = "https://test.example.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_teacher(phone: str = PHONE, name: str = "Mrs. Okafor"):
    """Register a teacher in the in-memory store and return the record."""
    return save_teacher(phone, name)


def _cleanup():
    """Clear in-memory stores between tests that mutate state."""
    _mem_teachers.clear()

    # Clear threads, sessions, homework, quiz, lesson history stores
    from classgen.data.homework import _mem_homework
    from classgen.data.lessons import _mem_lesson_history
    from classgen.data.parents import _mem_parent_subs
    from classgen.data.quiz import _mem_submissions
    from classgen.data.sessions import _mem_sessions
    from classgen.data.threads import _mem_active_threads

    _mem_active_threads.clear()
    _mem_sessions.clear()
    _mem_homework.clear()
    _mem_submissions.clear()
    _mem_lesson_history.clear()
    _mem_parent_subs.clear()


# ---------------------------------------------------------------------------
# Greeting commands
# ---------------------------------------------------------------------------


class TestGreetings:
    """Greetings are short-circuited before command dispatch to save LLM tokens."""

    def setup_method(self):
        _cleanup()

    def test_hi(self):
        result = handle_command("hi", PHONE, BASE)
        assert result is not None
        assert "Welcome to ClassGen" in result.reply

    def test_hello(self):
        result = handle_command("hello", PHONE, BASE)
        assert result is not None
        assert "Welcome to ClassGen" in result.reply

    def test_hey(self):
        result = handle_command("hey", PHONE, BASE)
        assert result is not None
        assert "Welcome" in result.reply

    def test_good_morning(self):
        result = handle_command("good morning", PHONE, BASE)
        assert result is not None
        assert "Welcome" in result.reply

    def test_greeting_case_insensitive(self):
        """Greetings should match regardless of case."""
        result = handle_command("HELLO", PHONE, BASE)
        assert result is not None
        assert "Welcome" in result.reply


# ---------------------------------------------------------------------------
# Session commands
# ---------------------------------------------------------------------------


class TestSessionCommands:
    def setup_method(self):
        _cleanup()

    def test_reset(self):
        """'reset' creates a new thread and returns session_action='reset'."""
        result = handle_command("reset", PHONE, BASE)
        assert result is not None
        assert result.session_action == "reset"
        assert result.new_thread_id is not None
        assert PHONE in result.new_thread_id
        assert "fresh" in result.reply.lower() or "starting" in result.reply.lower()

    def test_new(self):
        result = handle_command("new", PHONE, BASE)
        assert result is not None
        assert result.session_action == "reset"
        assert result.new_thread_id is not None

    def test_new_lesson(self):
        result = handle_command("new lesson", PHONE, BASE)
        assert result is not None
        assert result.session_action == "reset"

    def test_start_over(self):
        result = handle_command("start over", PHONE, BASE)
        assert result is not None
        assert result.session_action == "reset"


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


class TestHelp:
    def setup_method(self):
        _cleanup()

    def test_help(self):
        """'help' returns a structured command list."""
        result = handle_command("help", PHONE, BASE)
        assert result is not None
        assert "Commands" in result.reply

    def test_commands_alias(self):
        result = handle_command("commands", PHONE, BASE)
        assert result is not None
        assert "Commands" in result.reply

    def test_menu_alias(self):
        result = handle_command("menu", PHONE, BASE)
        assert result is not None
        assert "Commands" in result.reply


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def setup_method(self):
        _cleanup()

    def test_register_with_name(self):
        """'register Mrs. Okafor' creates a teacher and returns profile URL."""
        result = handle_command("register Mrs. Okafor", PHONE, BASE)
        assert result is not None
        assert "Mrs. Okafor" in result.reply
        assert f"{BASE}/t/" in result.reply
        assert result.session_action == "register"

    def test_register_no_name(self):
        """'register' alone (no name) prompts the user to include a name."""
        result = handle_command("register", PHONE, BASE)
        assert result is not None
        assert "register" in result.reply.lower()
        assert "Name" in result.reply or "name" in result.reply

    def test_register_short_name(self):
        """A single-character name is rejected with a prompt."""
        result = handle_command("register X", PHONE, BASE)
        assert result is not None
        assert "include your name" in result.reply.lower()

    def test_register_already_registered(self):
        """Bare 'register' when already registered shows existing profile."""
        _register_teacher()
        result = handle_command("register", PHONE, BASE)
        assert result is not None
        assert "already registered" in result.reply.lower()

    def test_i_am_alias(self):
        """'I am Mrs. Okafor' also registers."""
        result = handle_command("I am Mrs. Okafor", PHONE, BASE)
        assert result is not None
        assert "Mrs. Okafor" in result.reply
        assert result.session_action == "register"


# ---------------------------------------------------------------------------
# My page / profile
# ---------------------------------------------------------------------------


class TestMyPage:
    def setup_method(self):
        _cleanup()

    def test_my_page_registered(self):
        """Registered teacher gets their profile URL."""
        _register_teacher()
        result = handle_command("my page", PHONE, BASE)
        assert result is not None
        assert f"{BASE}/t/" in result.reply

    def test_my_page_unregistered(self):
        """Unregistered teacher is told to register first."""
        result = handle_command("my page", PHONE, BASE)
        assert result is not None
        assert "register" in result.reply.lower()
        assert "haven't" in result.reply.lower() or "not" in result.reply.lower()

    def test_profile_alias(self):
        result = handle_command("profile", PHONE, BASE)
        assert result is not None


# ---------------------------------------------------------------------------
# Add class
# ---------------------------------------------------------------------------


class TestAddClass:
    def setup_method(self):
        _cleanup()

    def test_add_class(self):
        """'add class: SS2 Biology' adds the class to the teacher's profile."""
        _register_teacher()
        result = handle_command("add class: SS2 Biology", PHONE, BASE)
        assert result is not None
        assert "SS2 Biology" in result.reply

    def test_add_class_without_colon(self):
        """'add class SS2 Biology' (no colon) also works."""
        _register_teacher()
        result = handle_command("add class SS2 Biology", PHONE, BASE)
        assert result is not None
        assert "SS2 Biology" in result.reply

    def test_add_class_not_registered(self):
        result = handle_command("add class: SS2 Biology", PHONE, BASE)
        assert result is not None
        assert "register" in result.reply.lower()


# ---------------------------------------------------------------------------
# My codes
# ---------------------------------------------------------------------------


class TestMyCodes:
    def setup_method(self):
        _cleanup()

    def test_my_codes_empty(self):
        """'my codes' with no generated lessons returns a helpful message."""
        result = handle_command("my codes", PHONE, BASE)
        assert result is not None
        assert "No homework codes" in result.reply or "no homework" in result.reply.lower()

    def test_my_codes_with_codes(self):
        """'my codes' lists homework codes when they exist."""
        from classgen.data.homework import save_homework_code

        save_homework_code(
            "TEST01",
            "thread1",
            "lesson content",
            [],
            "hw block",
            teacher_phone=PHONE,
        )
        result = handle_command("my codes", PHONE, BASE)
        assert result is not None
        assert "TEST01" in result.reply


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class TestResults:
    def setup_method(self):
        _cleanup()

    def test_results_no_submissions(self):
        """'results CODE' with no quiz submissions reports empty."""
        result = handle_command("results MATH42", PHONE, BASE)
        assert result is not None
        assert "No submissions" in result.reply or "no submissions" in result.reply.lower()

    def test_results_with_submissions(self):
        """'results CODE' with submissions shows count and average."""
        from classgen.data.quiz import save_quiz_submission

        save_quiz_submission("BIO01", "Amina", "SS2", [1, 0], 3, 5)
        save_quiz_submission("BIO01", "Chidi", "SS2", [1, 1], 5, 5)
        result = handle_command("results BIO01", PHONE, BASE)
        assert result is not None
        assert "BIO01" in result.reply
        assert "2" in result.reply  # 2 students

    def test_results_bare(self):
        """'results' without a code gives usage instructions."""
        result = handle_command("results", PHONE, BASE)
        assert result is not None
        assert "results CODE" in result.reply


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


class TestLeaderboard:
    def setup_method(self):
        _cleanup()

    def test_leaderboard_no_submissions(self):
        result = handle_command("leaderboard MATH42", PHONE, BASE)
        assert result is not None
        assert "No submissions" in result.reply or "no submissions" in result.reply.lower()

    def test_leaderboard_with_submissions(self):
        from classgen.data.quiz import save_quiz_submission

        save_quiz_submission("LDR01", "Amina", "SS2", [1], 5, 5)
        save_quiz_submission("LDR01", "Chidi", "SS2", [0], 3, 5)
        result = handle_command("leaderboard LDR01", PHONE, BASE)
        assert result is not None
        assert "LDR01" in result.reply
        assert "Amina" in result.reply

    def test_leaderboard_bare(self):
        """Bare 'leaderboard' gives usage instructions."""
        result = handle_command("leaderboard", PHONE, BASE)
        assert result is not None
        assert "leaderboard CODE" in result.reply


# ---------------------------------------------------------------------------
# Student progress
# ---------------------------------------------------------------------------


class TestProgress:
    def setup_method(self):
        _cleanup()

    def test_progress_no_history(self):
        """'progress Amina SS2' with no quiz history says none found."""
        result = handle_command("progress Amina SS2", PHONE, BASE)
        assert result is not None
        assert (
            "No quiz history" in result.reply
            or "no history" in result.reply.lower()
            or "no quiz" in result.reply.lower()
        )

    def test_progress_with_history(self):
        from classgen.data.quiz import save_quiz_submission

        save_quiz_submission("PRG01", "Amina", "SS2", [1], 4, 5)
        result = handle_command("progress Amina SS2", PHONE, BASE)
        assert result is not None
        assert "Amina" in result.reply
        assert "PRG01" in result.reply


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    def setup_method(self):
        _cleanup()

    def test_stats_registered(self):
        """Registered teacher sees their lesson generation stats."""
        _register_teacher()
        result = handle_command("stats", PHONE, BASE)
        assert result is not None
        assert "Stats" in result.reply or "stats" in result.reply.lower()

    def test_stats_unregistered(self):
        result = handle_command("stats", PHONE, BASE)
        assert result is not None
        assert "register" in result.reply.lower()


# ---------------------------------------------------------------------------
# Study mode
# ---------------------------------------------------------------------------


class TestStudyMode:
    def setup_method(self):
        _cleanup()

    def test_study_topic(self):
        """'study Photosynthesis' returns session_action='study' for LLM handling."""
        result = handle_command("study Photosynthesis", PHONE, BASE)
        assert result is not None
        assert result.session_action == "study"
        # The topic is passed through new_thread_id
        assert "Photosynthesis" in (result.new_thread_id or "")


# ---------------------------------------------------------------------------
# Suggest
# ---------------------------------------------------------------------------


class TestSuggest:
    def setup_method(self):
        _cleanup()

    def test_suggest_with_classes(self):
        """'suggest' (bare) lists the teacher's registered classes."""
        _register_teacher()
        from classgen.data.teachers import add_teacher_class

        add_teacher_class(PHONE, "SS2 Biology")

        result = handle_command("suggest", PHONE, BASE)
        assert result is not None
        assert "SS2 Biology" in result.reply

    def test_suggest_specific_class(self):
        """'suggest SS2 Biology' lists curriculum topics."""
        _register_teacher()
        result = handle_command("suggest SS2 Biology", PHONE, BASE)
        assert result is not None
        # Should list actual WAEC curriculum topics
        assert "SS2" in result.reply or "Biology" in result.reply

    def test_suggest_no_classes(self):
        """'suggest' with no classes registered prompts to add one."""
        _register_teacher()
        result = handle_command("suggest", PHONE, BASE)
        assert result is not None
        assert "add class" in result.reply.lower() or "add a class" in result.reply.lower()

    def test_suggest_not_registered(self):
        result = handle_command("suggest", PHONE, BASE)
        assert result is not None
        assert "register" in result.reply.lower()


# ---------------------------------------------------------------------------
# Covered
# ---------------------------------------------------------------------------


class TestCovered:
    def setup_method(self):
        _cleanup()

    def test_covered_no_lessons(self):
        """'covered SS2 Biology' with no generated lessons says none."""
        result = handle_command("covered SS2 Biology", PHONE, BASE)
        assert result is not None
        assert "No lessons" in result.reply or "no lessons" in result.reply.lower()

    def test_covered_with_lessons(self):
        """After generating lessons, 'covered' lists the topics."""
        from classgen.data.lessons import log_lesson_generated

        log_lesson_generated(PHONE, "Biology", "Photosynthesis", "SS2")
        result = handle_command("covered SS2 Biology", PHONE, BASE)
        assert result is not None
        assert "Photosynthesis" in result.reply


# ---------------------------------------------------------------------------
# Fall-through to LLM
# ---------------------------------------------------------------------------


class TestFallThrough:
    """Unknown text that isn't a command returns None so the LLM handles it."""

    def setup_method(self):
        _cleanup()

    def test_unknown_text_returns_none(self):
        result = handle_command("SS2 Biology: Photosynthesis", PHONE, BASE)
        assert result is None

    def test_random_sentence_returns_none(self):
        result = handle_command("Tell me about the solar system", PHONE, BASE)
        assert result is None

    def test_empty_string_returns_none(self):
        """An empty string after strip is not a greeting or command."""
        result = handle_command("   ", PHONE, BASE)
        assert result is None
