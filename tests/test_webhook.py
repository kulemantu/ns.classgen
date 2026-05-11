"""Tests for the Twilio WhatsApp webhook handler.

Verifies WhatsApp-specific behaviors: voice note rejection, empty body
handling, greeting short-circuit, media type detection, and the
_whatsapp_summary formatter that condenses lesson packs for WhatsApp's
character limits.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.api.webhook import _whatsapp_summary

client = TestClient(app)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_LESSON = (
    "[BLOCK_START_OPENER]\n"
    "Title: **Kitchen Water Cycle**\n"
    "Summary: Boil water and watch the cycle.\n"
    "Details: Steam rises, condenses on cold plate.\n"
    "[BLOCK_END]\n\n"
    "[BLOCK_START_EXPLAIN]\n"
    "Title: **Evaporation and Condensation**\n"
    "Summary: Two key processes in the water cycle.\n"
    "Details: Evaporation turns liquid to gas.\n"
    "[BLOCK_END]\n\n"
    "[BLOCK_START_ACTIVITY]\n"
    "Title: **Draw the Cycle**\n"
    "Summary: Students draw and label the water cycle.\n"
    "Details: Use arrows to show movement.\n"
    "[BLOCK_END]\n\n"
    "[BLOCK_START_HOMEWORK]\n"
    "Title: **Water Detective**\n"
    "Summary: Observe water cycle at home.\n"
    "Details: Record three observations.\n"
    "[BLOCK_END]\n\n"
    "[BLOCK_START_TEACHER_NOTES]\n"
    "Title: **Common Misconceptions**\n"
    "Summary: Students often confuse evaporation with boiling.\n"
    "Details: Clarify that evaporation happens at any temperature.\n"
    "[BLOCK_END]"
)


# ---------------------------------------------------------------------------
# Voice note handling
# ---------------------------------------------------------------------------


class TestVoiceNoteRejection:
    """Voice notes (audio media) should be rejected with a helpful message
    rather than sent to the LLM or crashing."""

    def test_voice_note_rejected(self):
        """Audio media type triggers graceful rejection."""
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "",
                "MediaUrl0": "https://api.twilio.com/audio.ogg",
                "MediaContentType0": "audio/ogg",
            },
        )
        assert response.status_code == 200
        assert "Voice notes" in response.text
        assert "application/xml" in response.headers["content-type"]

    def test_voice_note_with_body_still_rejected(self):
        """Even if Body is present alongside audio, the audio triggers rejection."""
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "some text",
                "MediaUrl0": "https://api.twilio.com/voice.mp3",
                "MediaContentType0": "audio/mpeg",
            },
        )
        assert response.status_code == 200
        assert "Voice notes" in response.text


# ---------------------------------------------------------------------------
# Empty body
# ---------------------------------------------------------------------------


class TestEmptyBody:
    """An empty message (e.g., just opening the chat) should return
    the welcome message without calling the LLM."""

    def test_empty_body_welcome(self):
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "",
            },
        )
        assert response.status_code == 200
        assert "Welcome to ClassGen" in response.text

    def test_whitespace_only_welcome(self):
        """Whitespace-only body is treated as empty."""
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "   ",
            },
        )
        assert response.status_code == 200
        assert "Welcome to ClassGen" in response.text


# ---------------------------------------------------------------------------
# Greeting (no LLM call)
# ---------------------------------------------------------------------------


class TestGreetingBypass:
    """Greetings are handled by the command router and must not trigger
    an LLM call."""

    @patch("classgen.api.webhook.call_openrouter", new_callable=AsyncMock)
    def test_hello_no_llm(self, mock_llm):
        """'hello' returns a welcome message without calling call_openrouter."""
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "hello",
            },
        )
        assert response.status_code == 200
        assert "Welcome to ClassGen" in response.text
        mock_llm.assert_not_called()

    @patch("classgen.api.webhook.call_openrouter", new_callable=AsyncMock)
    def test_help_no_llm(self, mock_llm):
        """'help' returns the command menu without calling call_openrouter."""
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "help",
            },
        )
        assert response.status_code == 200
        assert "Commands" in response.text
        mock_llm.assert_not_called()


# ---------------------------------------------------------------------------
# Non-audio media
# ---------------------------------------------------------------------------


class TestNonAudioMedia:
    """Image or document attachments (non-audio) should NOT be rejected
    as voice notes. They fall through to normal processing."""

    @patch("classgen.api.webhook.check_usage")
    @patch("classgen.api.webhook.log_usage")
    @patch("classgen.api.webhook.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch(
        "classgen.api.chat.call_openrouter",
        new_callable=AsyncMock,
        return_value="This is a clarifying reply.",
    )
    def test_image_media_not_rejected(
        self,
        mock_llm,
        mock_log,
        mock_hist,
        mock_pdf,
        mock_cmd,
        mock_log_usage,
        mock_check,
    ):
        """An image attachment with text body is processed normally."""
        mock_check.return_value = type(
            "U",
            (),
            {
                "allowed": True,
                "remaining": 5,
                "tier": "free",
                "message": "",
            },
        )()
        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "Check this diagram",
                "MediaUrl0": "https://api.twilio.com/image.jpg",
                "MediaContentType0": "image/jpeg",
            },
        )
        assert response.status_code == 200
        # Should NOT contain the voice note rejection
        assert "Voice notes" not in response.text
        # The LLM was called to process the message
        mock_llm.assert_called()


# ---------------------------------------------------------------------------
# Student bridge — homework-code short-circuit
# ---------------------------------------------------------------------------


class TestHomeworkCodeStudentBridge:
    """When a WhatsApp number sends JUST a homework code (`MATH42` shape),
    reply with the link to the homework page so the student opens it in
    their browser. Channel-asymmetry by design: WhatsApp's role for
    students is to bridge to the page, not replicate the UI."""

    def setup_method(self):
        from classgen.data.homework import _mem_homework
        from classgen.data.teachers import _mem_teachers

        _mem_homework.clear()
        _mem_teachers.clear()

    def teardown_method(self):
        from classgen.data.homework import _mem_homework
        from classgen.data.teachers import _mem_teachers

        _mem_homework.clear()
        _mem_teachers.clear()

    def _seed_code(self, code: str, teacher_phone: str = "") -> None:
        from classgen.data.homework import save_homework_code

        save_homework_code(
            code,
            "thread_seed",
            "raw",
            [{"question": "Q", "options": ["A", "B", "C", "D"], "correct": 0}],
            "Title: Test\nDetails: Test homework",
            teacher_phone=teacher_phone,
        )

    def test_known_code_returns_link_with_teacher_name(self):
        """A student texting the code gets a link + the teacher's name."""
        from classgen.data.teachers import save_teacher

        save_teacher("+23488776655", name="Mrs. Okafor", country="Nigeria")
        self._seed_code("MATH42", teacher_phone="+23488776655")

        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+27725550199", "Body": "MATH42"},
        )

        assert response.status_code == 200
        body = response.text
        assert "MATH42" in body
        assert "Mrs. Okafor" in body
        assert "/h/MATH42" in body
        # Must NOT route through teacher onboarding for the student
        assert "Reply" not in body or "YES" not in body
        assert "Welcome to ClassGen" not in body

    def test_known_code_works_without_teacher(self):
        """Legacy / anonymous codes (no teacher_phone) still bridge cleanly."""
        self._seed_code("ANON42")

        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+27725550111", "Body": "ANON42"},
        )

        assert response.status_code == 200
        body = response.text
        assert "ANON42" in body
        assert "/h/ANON42" in body
        # No teacher name should appear when no teacher is registered
        assert "set by" not in body.lower()

    def test_unknown_code_returns_helpful_message_not_onboarding(self):
        """A code-shaped string that doesn't exist gets a student-friendly
        'not found' message — never the teacher welcome flow."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+27725550222", "Body": "WXYZ99"},
        )

        assert response.status_code == 200
        body = response.text
        assert "couldn't find" in body.lower() or "couldn&#39;t find" in body.lower()
        assert "WXYZ99" in body
        assert "Welcome to ClassGen" not in body  # never the onboarding path

    def test_case_insensitive_code(self):
        """A student texting 'math42' (lowercase) is treated identically."""
        self._seed_code("MATH42")

        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+27725550333", "Body": "math42"},
        )

        assert response.status_code == 200
        assert "/h/MATH42" in response.text

    def test_non_code_message_falls_through_normally(self):
        """A body that doesn't match the code shape (`MATH42` exactly) still
        hits the existing onboarding/command flow — we haven't broken anything."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+27725550444", "Body": "Help me with MATH42"},
        )

        assert response.status_code == 200
        body = response.text
        # Code-bridge path requires the ENTIRE body to match. "Help me with
        # MATH42" should fall through to onboarding (this number is not
        # onboarded, so it sees the welcome).
        assert "/h/MATH42" not in body


# ---------------------------------------------------------------------------
# LLM unavailable -> friendly TwiML retry message
# ---------------------------------------------------------------------------


class TestLLMUnavailableTwiML:
    """When the LLM call exhausts retries inside `_generate_lesson`, the
    webhook catches `LLMUnavailableError` and replies with a TwiML message
    that asks the teacher to send the message again. Channel-appropriate UX
    for the same failure that returns a 502 envelope on the web endpoint."""

    @patch("classgen.api.webhook.check_usage")
    @patch("classgen.api.webhook.log_usage")
    @patch("classgen.api.webhook.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch(
        "classgen.api.chat.call_openrouter",
        new_callable=AsyncMock,
        return_value=None,  # exhausted-retries sentinel inside _generate_lesson
    )
    def test_returns_friendly_twiml_when_llm_returns_none(
        self,
        mock_llm,
        mock_log,
        mock_hist,
        mock_pdf,
        mock_cmd,
        mock_log_usage,
        mock_check,
    ):
        """call_openrouter returning None makes `_generate_lesson` raise
        LLMUnavailableError; the webhook should swallow it and reply with
        the 'Couldn't reach the AI just now' TwiML, not 500 or empty body."""
        mock_check.return_value = type(
            "U",
            (),
            {"allowed": True, "remaining": 5, "tier": "free", "message": ""},
        )()

        response = client.post(
            "/webhook/twilio",
            data={
                "From": "whatsapp:+23412345678",
                "Body": "SS2 Biology: Photosynthesis, 40 mins",
            },
        )

        assert response.status_code == 200  # never bleed 5xx to Twilio
        assert "Couldn't reach the AI" in response.text
        assert "send your message again" in response.text
        # The PDF generator must NOT have been called (no content produced)
        mock_pdf.assert_not_called()


# ---------------------------------------------------------------------------
# _whatsapp_summary format
# ---------------------------------------------------------------------------


class TestWhatsappSummary:
    """_whatsapp_summary condenses a full lesson pack into a WhatsApp-friendly
    message with block titles and an optional homework code link."""

    def test_all_block_titles_present(self):
        """Each block type label appears in the summary."""
        summary = _whatsapp_summary(SAMPLE_LESSON, "WATR42", "https://x.com")
        assert "Hook" in summary  # OPENER -> Hook
        assert "Concept" in summary  # EXPLAIN -> Concept
        assert "Activity" in summary  # ACTIVITY -> Activity
        assert "Homework" in summary  # HOMEWORK -> Homework
        assert "Notes" in summary  # TEACHER_NOTES -> Notes

    def test_homework_code_included(self):
        """When a homework code is provided, it appears with the student URL."""
        summary = _whatsapp_summary(SAMPLE_LESSON, "WATR42", "https://test.example.com")
        assert "WATR42" in summary
        assert "https://test.example.com/h/WATR42" in summary

    def test_no_homework_code(self):
        """When homework_code is None, no code line appears."""
        summary = _whatsapp_summary(SAMPLE_LESSON, None, "https://x.com")
        assert "Homework Code:" not in summary
        assert "/h/" not in summary

    def test_pdf_attachment_note(self):
        """The summary always ends with a note about the PDF attachment."""
        summary = _whatsapp_summary(SAMPLE_LESSON, None, "https://x.com")
        assert "PDF" in summary

    def test_block_title_text_extracted(self):
        """The actual title text (not just labels) is included in summary."""
        summary = _whatsapp_summary(SAMPLE_LESSON, None, "https://x.com")
        assert "Kitchen Water Cycle" in summary
        assert "Draw the Cycle" in summary

    def test_classgen_header(self):
        """The summary starts with a ClassGen header."""
        summary = _whatsapp_summary(SAMPLE_LESSON, None, "https://x.com")
        assert "ClassGen Lesson Pack" in summary
