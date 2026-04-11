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
