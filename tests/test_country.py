"""Tests for the teacher-country feature.

Covers the country_from_phone helper, data-layer persistence,
API endpoints (PATCH /api/teacher/country, GET /api/teacher/countries),
WhatsApp onboarding auto-detection, and LLM prompt injection.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.data.teachers import (
    _mem_teachers,
    get_teacher_by_phone,
    save_teacher,
    update_teacher_country,
)
from classgen.i18n import SUPPORTED_COUNTRIES, country_from_phone

client = TestClient(app)


# ---------------------------------------------------------------------------
# country_from_phone helper
# ---------------------------------------------------------------------------


class TestCountryFromPhone:
    """Infer country name from a phone number's country code prefix."""

    def test_nigeria(self):
        assert country_from_phone("+2348012345678") == "Nigeria"

    def test_kenya(self):
        assert country_from_phone("+254712345678") == "Kenya"

    def test_south_africa(self):
        """+27 is shorter than +270-something codes — must match by longest prefix."""
        assert country_from_phone("+27821234567") == "South Africa"

    def test_ghana(self):
        assert country_from_phone("+233241234567") == "Ghana"

    def test_us_fallback(self):
        assert country_from_phone("+14155551212") == "United States"

    def test_whatsapp_prefix_stripped(self):
        """The 'whatsapp:' Twilio prefix is stripped before matching."""
        assert country_from_phone("whatsapp:+254712345678") == "Kenya"

    def test_unknown_prefix_returns_empty(self):
        """An unmatched country code returns an empty string, not None."""
        result = country_from_phone("+9999999999")
        assert result == ""

    def test_empty_phone_returns_empty(self):
        assert country_from_phone("") == ""

    def test_longest_prefix_wins(self):
        """+254 (Kenya) must win over +2 (if it existed) — longest prefix match."""
        # +234 (Nigeria) is longer than +2, so Nigeria must be chosen.
        assert country_from_phone("+2348012345678") == "Nigeria"
        assert country_from_phone("+254712345678") == "Kenya"


# ---------------------------------------------------------------------------
# Teacher data layer — country persistence
# ---------------------------------------------------------------------------


class TestTeacherCountryDataLayer:
    """save_teacher(country=...) and update_teacher_country roundtrips."""

    def setup_method(self):
        _mem_teachers.clear()

    def teardown_method(self):
        _mem_teachers.clear()

    @patch("classgen.data.teachers.supabase", None)
    def test_save_teacher_persists_country(self):
        teacher = save_teacher(
            phone="+2348012345678",
            name="Mrs. Okafor",
            country="Nigeria",
        )
        assert teacher["country"] == "Nigeria"

    @patch("classgen.data.teachers.supabase", None)
    def test_save_teacher_default_country_empty(self):
        teacher = save_teacher(phone="+2348012345678", name="Mrs. Okafor")
        assert teacher["country"] == ""

    @patch("classgen.data.teachers.supabase", None)
    def test_update_teacher_country_roundtrip(self):
        save_teacher(phone="+2348012345678", name="Mrs. Okafor")
        updated = update_teacher_country("+2348012345678", "Nigeria")
        assert updated is not None
        assert updated["country"] == "Nigeria"

        # Confirm persistence via a fresh read
        fresh = get_teacher_by_phone("+2348012345678")
        assert fresh is not None
        assert fresh["country"] == "Nigeria"

    @patch("classgen.data.teachers.supabase", None)
    def test_update_teacher_country_missing_returns_none(self):
        assert update_teacher_country("+9999999999", "Nigeria") is None

    @patch("classgen.data.teachers.supabase", None)
    def test_resave_with_new_country_overwrites(self):
        """Re-saving an existing teacher with a non-empty country updates it."""
        save_teacher(
            phone="+2348012345678",
            name="Mrs. Okafor",
            country="Nigeria",
        )
        save_teacher(
            phone="+2348012345678",
            name="Mrs. Okafor",
            country="Ghana",
        )
        teacher = get_teacher_by_phone("+2348012345678")
        assert teacher is not None
        assert teacher["country"] == "Ghana"

    @patch("classgen.data.teachers.supabase", None)
    def test_resave_with_empty_country_preserves_existing(self):
        """Re-saving without a country (empty string) must not clobber the previous value."""
        save_teacher(
            phone="+2348012345678",
            name="Mrs. Okafor",
            country="Nigeria",
        )
        save_teacher(phone="+2348012345678", name="Mrs. Okafor")
        teacher = get_teacher_by_phone("+2348012345678")
        assert teacher is not None
        assert teacher["country"] == "Nigeria"


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestCountriesListEndpoint:
    def test_returns_supported_countries(self):
        response = client.get("/api/teacher/countries")
        assert response.status_code == 200
        data = response.json()
        assert "countries" in data
        assert isinstance(data["countries"], list)
        assert data["countries"] == SUPPORTED_COUNTRIES

    def test_includes_key_markets(self):
        response = client.get("/api/teacher/countries")
        countries = response.json()["countries"]
        for expected in ("Nigeria", "Kenya", "Ghana", "South Africa"):
            assert expected in countries


class TestUpdateCountryEndpoint:
    @patch("classgen.api.teacher.update_teacher_country")
    def test_success(self, mock_update):
        mock_update.return_value = {"country": "Nigeria"}
        response = client.patch(
            "/api/teacher/country",
            json={"thread_id": "chat_abc", "country": "Nigeria"},
        )
        assert response.status_code == 200
        assert response.json()["country"] == "Nigeria"
        mock_update.assert_called_once_with("chat_abc", "Nigeria")

    @patch("classgen.api.teacher.update_teacher_country")
    def test_teacher_not_found(self, mock_update):
        mock_update.return_value = None
        response = client.patch(
            "/api/teacher/country",
            json={"thread_id": "chat_missing", "country": "Nigeria"},
        )
        assert response.status_code == 404
        assert "error" in response.json()

    def test_country_required(self):
        """Pydantic validation rejects empty / too-short country values."""
        response = client.patch(
            "/api/teacher/country",
            json={"thread_id": "chat_abc", "country": "x"},
        )
        assert response.status_code == 422


class TestTeacherProfileIncludesCountry:
    @patch("classgen.api.teacher.list_homework_codes_for_teacher", return_value=[])
    @patch(
        "classgen.api.teacher.get_teacher_lesson_stats",
        return_value={"total": 0, "this_week": 0, "this_month": 0},
    )
    @patch("classgen.api.teacher.get_teacher_by_phone")
    def test_profile_returns_country(self, mock_get, mock_stats, mock_codes):
        mock_get.return_value = {
            "name": "Mrs. Okafor",
            "slug": "mrs-okafor",
            "classes": [],
            "country": "Nigeria",
        }
        response = client.get("/api/teacher/profile?thread_id=chat_abc")
        assert response.status_code == 200
        assert response.json()["teacher"]["country"] == "Nigeria"


# ---------------------------------------------------------------------------
# WhatsApp onboarding auto-detect
# ---------------------------------------------------------------------------


class TestWhatsAppOnboardingCountry:
    """Replying YES during WhatsApp onboarding saves teacher with auto-detected country."""

    @patch("classgen.api.webhook.mark_onboarded")
    @patch("classgen.api.webhook.save_teacher")
    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_yes_saves_country_from_phone(
        self, mock_teacher, mock_onboarded, mock_save, mock_mark
    ):
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+2348012345678", "Body": "YES"},
        )
        assert response.status_code == 200
        mock_save.assert_called_once()
        # kwargs may differ, but country should be passed as keyword
        _, kwargs = mock_save.call_args
        assert kwargs.get("country") == "Nigeria"

    @patch("classgen.api.webhook.mark_onboarded")
    @patch("classgen.api.webhook.save_teacher")
    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_yes_unknown_country_saves_empty(
        self, mock_teacher, mock_onboarded, mock_save, mock_mark
    ):
        """Unknown country code still onboards; country just ends up empty."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+9999999999", "Body": "YES"},
        )
        assert response.status_code == 200
        mock_save.assert_called_once()
        _, kwargs = mock_save.call_args
        assert kwargs.get("country") == ""


# ---------------------------------------------------------------------------
# Chat prompt injection
# ---------------------------------------------------------------------------


SAMPLE_LESSON = (
    "[BLOCK_START_OPENER]\nTitle: T\nSummary: S\nDetails: D\n[BLOCK_END]\n"
    "[BLOCK_START_EXPLAIN]\nTitle: T\nSummary: S\nDetails: D\n[BLOCK_END]\n"
    "[BLOCK_START_ACTIVITY]\nTitle: T\nSummary: S\nDetails: D\n[BLOCK_END]\n"
    "[BLOCK_START_HOMEWORK]\nTitle: T\nSummary: S\nDetails: D\n[BLOCK_END]\n"
    "[BLOCK_START_TEACHER_NOTES]\nTitle: T\nSummary: S\nDetails: D\n[BLOCK_END]"
)


class TestChatPromptCountryInjection:
    """The teacher's country is injected into the LLM prompt when set."""

    @patch("classgen.api.chat.get_teacher_by_phone")
    @patch("classgen.api.chat.check_usage")
    @patch("classgen.api.chat.log_usage")
    @patch("classgen.api.chat.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="f.pdf")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_homework_code", return_value="HW0001")
    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.data.teachers.get_teacher_by_phone")
    def test_country_in_prompt_when_set(
        self,
        mock_get_teacher_data,
        mock_save_hw,
        mock_gen_code,
        mock_llm,
        mock_log,
        mock_hist,
        mock_pdf,
        mock_cmd,
        mock_log_usage,
        mock_check,
        mock_get_teacher_api,
        monkeypatch,
    ):
        monkeypatch.delenv("FF_STRUCTURED_OUTPUT", raising=False)
        teacher = {
            "name": "Mrs. W",
            "slug": "mrs-w",
            "classes": [],
            "country": "Nigeria",
        }
        mock_get_teacher_api.return_value = teacher
        mock_get_teacher_data.return_value = teacher
        mock_check.return_value = type(
            "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
        )()
        mock_llm.side_effect = [SAMPLE_LESSON, "[]"]

        response = client.post(
            "/api/chat",
            json={
                "message": "SS2 Biology: Photosynthesis",
                "thread_id": "chat_ng",
            },
        )
        assert response.status_code == 200
        assert mock_llm.called
        # First LLM call is the lesson generation. Args: (system_prompt, user_prompt)
        first_call = mock_llm.call_args_list[0]
        user_prompt = first_call.args[1] if len(first_call.args) > 1 else first_call.kwargs.get(
            "prompt", ""
        )
        assert "Nigeria" in user_prompt
        assert "Teacher's country: Nigeria" in user_prompt

    @patch("classgen.api.chat.get_teacher_by_phone")
    @patch("classgen.api.chat.check_usage")
    @patch("classgen.api.chat.log_usage")
    @patch("classgen.api.chat.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="f.pdf")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_homework_code", return_value="HW0002")
    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.data.teachers.get_teacher_by_phone")
    def test_no_country_context_when_unset(
        self,
        mock_get_teacher_data,
        mock_save_hw,
        mock_gen_code,
        mock_llm,
        mock_log,
        mock_hist,
        mock_pdf,
        mock_cmd,
        mock_log_usage,
        mock_check,
        mock_get_teacher_api,
        monkeypatch,
    ):
        monkeypatch.delenv("FF_STRUCTURED_OUTPUT", raising=False)
        teacher = {"name": "Mrs. W", "slug": "mrs-w", "classes": [], "country": ""}
        mock_get_teacher_api.return_value = teacher
        mock_get_teacher_data.return_value = teacher
        mock_check.return_value = type(
            "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
        )()
        mock_llm.side_effect = [SAMPLE_LESSON, "[]"]

        response = client.post(
            "/api/chat",
            json={
                "message": "SS2 Biology: Photosynthesis",
                "thread_id": "chat_nocountry",
            },
        )
        assert response.status_code == 200
        first_call = mock_llm.call_args_list[0]
        user_prompt = first_call.args[1] if len(first_call.args) > 1 else first_call.kwargs.get(
            "prompt", ""
        )
        assert "Teacher's country:" not in user_prompt
