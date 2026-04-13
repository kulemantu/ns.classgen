"""Tests for the onboarding system — web intro, terms page, WhatsApp welcome, data layer."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.content.onboarding import ONBOARDING, whatsapp_welcome
from classgen.data.teachers import _mem_teachers, is_onboarded, mark_onboarded

client = TestClient(app)


# ---------------------------------------------------------------------------
# Onboarding content config
# ---------------------------------------------------------------------------


class TestOnboardingConfig:
    def test_has_required_keys(self):
        for key in ("brand", "tagline", "slides", "cta", "terms_url"):
            assert key in ONBOARDING

    def test_slides_count(self):
        assert len(ONBOARDING["slides"]) == 2

    def test_first_slide_has_examples(self):
        examples = ONBOARDING["slides"][0]["examples"]
        assert isinstance(examples, list)
        assert len(examples) == 4

    def test_second_slide_has_features(self):
        features = ONBOARDING["slides"][1]["features"]
        assert isinstance(features, list)
        assert len(features) == 3

    def test_terms_url(self):
        assert ONBOARDING["terms_url"] == "/terms"

    def test_brand_name(self):
        assert ONBOARDING["brand"] == "ClassGen"


class TestWhatsAppWelcome:
    def test_welcome_message_content(self):
        msg = whatsapp_welcome("https://classgen.ng")
        assert "ClassGen" in msg
        assert "YES" in msg
        assert "https://classgen.ng/terms" in msg
        assert "PDF" in msg

    def test_welcome_has_features(self):
        msg = whatsapp_welcome("https://example.com")
        assert "quiz" in msg.lower()
        assert "WhatsApp" in msg

    def test_welcome_has_help(self):
        msg = whatsapp_welcome("https://example.com")
        assert "HELP" in msg


# ---------------------------------------------------------------------------
# Terms page
# ---------------------------------------------------------------------------


class TestTermsPage:
    def test_terms_returns_200(self):
        response = client.get("/terms")
        assert response.status_code == 200

    def test_terms_has_content(self):
        response = client.get("/terms")
        html = response.text
        assert "Terms" in html
        assert "Privacy" in html
        assert "ClassGen" in html

    def test_terms_has_data_section(self):
        response = client.get("/terms")
        assert "What We Collect" in response.text

    def test_terms_has_contact(self):
        response = client.get("/terms")
        assert "help@dater.world" in response.text


# ---------------------------------------------------------------------------
# Web intro overlay
# ---------------------------------------------------------------------------


class TestIntroOverlay:
    def test_intro_overlay_exists(self):
        response = client.get("/")
        assert 'id="intro-overlay"' in response.text

    def test_intro_has_3_slides(self):
        response = client.get("/")
        assert response.text.count('class="intro-slide') >= 3

    def test_intro_dot_pagination(self):
        response = client.get("/")
        assert 'class="intro-dots"' in response.text
        assert response.text.count('class="intro-dot') >= 3

    def test_intro_skip_button(self):
        response = client.get("/")
        assert 'id="intro-skip"' in response.text

    def test_intro_cta_button(self):
        response = client.get("/")
        assert 'id="intro-cta"' in response.text

    def test_intro_terms_link(self):
        response = client.get("/")
        assert 'href="/terms"' in response.text

    def test_intro_localStorage_key(self):
        response = client.get("/")
        assert "classgen_intro_seen" in response.text

    def test_intro_content_object(self):
        response = client.get("/")
        assert "INTRO_CONTENT" in response.text

    def test_intro_touch_support(self):
        response = client.get("/")
        assert "touchstart" in response.text
        assert "touchend" in response.text

    def test_intro_brand_name(self):
        response = client.get("/")
        html = response.text
        assert 'class="intro-brand"' in html
        assert "ClassGen" in html

    def test_intro_feature_cards(self):
        response = client.get("/")
        assert response.text.count('class="intro-feature"') >= 3

    def test_intro_hidden_by_default(self):
        """Overlay starts with 'hidden' class (JS removes it for first visit)."""
        response = client.get("/")
        assert 'id="intro-overlay" class="hidden"' in response.text

    def test_intro_dm_serif_font(self):
        response = client.get("/")
        assert "DM+Serif+Display" in response.text
        assert "DM Serif Display" in response.text


# ---------------------------------------------------------------------------
# Onboarding data layer (in-memory)
# ---------------------------------------------------------------------------


class TestOnboardingDataLayer:
    def setup_method(self):
        _mem_teachers.clear()

    def teardown_method(self):
        _mem_teachers.clear()

    def test_is_onboarded_false_by_default(self):
        assert is_onboarded("+1234567890") is False

    def test_is_onboarded_false_no_teacher(self):
        assert is_onboarded("+9999999999") is False

    def test_mark_onboarded_sets_timestamp(self):
        _mem_teachers["+1234567890"] = {"phone": "+1234567890", "name": "Test"}
        mark_onboarded("+1234567890")
        assert is_onboarded("+1234567890") is True

    def test_is_onboarded_true_after_mark(self):
        _mem_teachers["+1234567890"] = {"phone": "+1234567890", "name": "Test"}
        assert is_onboarded("+1234567890") is False
        mark_onboarded("+1234567890")
        assert is_onboarded("+1234567890") is True

    def test_mark_returns_true(self):
        _mem_teachers["+1234567890"] = {"phone": "+1234567890", "name": "Test"}
        assert mark_onboarded("+1234567890") is True


# ---------------------------------------------------------------------------
# WhatsApp onboarding flow (webhook)
# ---------------------------------------------------------------------------


class TestWhatsAppOnboarding:
    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_new_user_gets_welcome(self, mock_teacher, mock_onboarded):
        """First message from unknown number returns welcome text."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+9999999999", "Body": "hello"},
        )
        assert response.status_code == 200
        assert "ClassGen" in response.text
        assert "YES" in response.text
        assert "/terms" in response.text

    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_welcome_includes_terms_link(self, mock_teacher, mock_onboarded):
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+9999999999", "Body": "test"},
        )
        assert "/terms" in response.text

    @patch("classgen.api.webhook.mark_onboarded")
    @patch("classgen.api.webhook.save_teacher")
    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_yes_reply_onboards(self, mock_teacher, mock_onboarded, mock_save, mock_mark):
        """Reply 'YES' creates teacher record and marks onboarded."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+9999999999", "Body": "YES"},
        )
        assert response.status_code == 200
        assert "all set" in response.text.lower()
        mock_save.assert_called_once()
        mock_mark.assert_called_once()

    @patch("classgen.api.webhook.is_onboarded", return_value=False)
    @patch("classgen.api.webhook.get_teacher_by_phone", return_value=None)
    def test_help_passes_through_when_not_onboarded(self, mock_teacher, mock_onboarded):
        """HELP command still works even before onboarding."""
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+9999999999", "Body": "help"},
        )
        assert response.status_code == 200
        assert "Commands" in response.text or "commands" in response.text

    @patch("classgen.api.webhook.check_usage")
    @patch("classgen.api.webhook.log_usage")
    @patch("classgen.api.webhook.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_homework_code", return_value="ONBR42")
    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.webhook.is_onboarded", return_value=True)
    def test_onboarded_user_proceeds_normally(
        self,
        mock_onboarded,
        mock_save_hw,
        mock_code,
        mock_llm,
        mock_log,
        mock_hist,
        mock_pdf,
        mock_cmd,
        mock_usage_log,
        mock_check,
    ):
        """Onboarded user skips welcome and gets normal lesson flow."""
        mock_check.return_value = type(
            "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
        )()
        mock_llm.side_effect = [
            "[BLOCK_START_OPENER]\nTitle: Test\nSummary: S\nDetails: D\n[BLOCK_END]",
            '[{"question":"Q","options":["A","B","C","D"],"correct":0}]',
        ]
        mock_pdf.return_value = "test.pdf"
        response = client.post(
            "/webhook/twilio",
            data={"From": "whatsapp:+1111111111", "Body": "SS1 Bio: Test"},
        )
        assert response.status_code == 200
        # Should NOT contain welcome/YES prompt
        assert "Reply *YES*" not in response.text
