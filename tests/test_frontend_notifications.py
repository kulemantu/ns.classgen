"""Tests for frontend notification and persistence features.

Validates that:
- The Notifications button was removed from the header HTML
- Push toggle remains in the settings sidebar HTML
- Toast element exists in the served HTML
- /api/config still works (used by frontend to decide notification strategy)
- Chat history localStorage keys are referenced in the JS
- The renderAiResponse / restoreConversation / notifyLesson functions exist
"""

from fastapi.testclient import TestClient

from classgen.api.app import app

client = TestClient(app)


class TestHeaderNotificationRemoved:
    """The notify-btn button was removed from the header HTML."""

    def test_no_notify_btn_element_in_header(self):
        """The <button id='notify-btn'> element should not exist."""
        response = client.get("/")
        html = response.text
        # The button element itself should be gone
        assert 'id="notify-btn"' not in html
        assert 'onclick="enableNotifications()">' not in html

    def test_profile_btn_still_in_header(self):
        response = client.get("/")
        assert 'id="profile-btn"' in response.text


class TestPushToggleInSettings:
    """Push notification toggle lives in the settings sidebar."""

    def test_push_toggle_in_sidebar(self):
        response = client.get("/")
        html = response.text
        assert "push-toggle" in html
        assert "Push notifications" in html
        assert "togglePush()" in html


class TestToastElement:
    """Toast notification element and styles are present."""

    def test_toast_div_exists(self):
        response = client.get("/")
        assert 'id="toast"' in response.text

    def test_toast_dark_background(self):
        """Toast uses dark slate background, not green."""
        response = client.get("/")
        assert "#1e293b" in response.text

    def test_toast_dark_mode_variant(self):
        response = client.get("/")
        assert '[data-theme="dark"] .toast' in response.text

    def test_toast_high_z_index(self):
        response = client.get("/")
        assert "z-index: 9999" in response.text


class TestFrontendFunctions:
    """Key JS functions exist in the served HTML."""

    def test_show_toast(self):
        response = client.get("/")
        assert "function showToast(" in response.text

    def test_notify_lesson(self):
        response = client.get("/")
        assert "function notifyLesson(" in response.text

    def test_render_ai_response(self):
        response = client.get("/")
        assert "function renderAiResponse(" in response.text

    def test_save_conversation(self):
        response = client.get("/")
        assert "function saveConversation(" in response.text

    def test_restore_conversation(self):
        response = client.get("/")
        assert "function restoreConversation(" in response.text

    def test_humanize(self):
        response = client.get("/")
        assert "function humanize(" in response.text

    def test_format_details(self):
        response = client.get("/")
        assert "function formatDetails(" in response.text


class TestLocalStorageKeys:
    """The JS references the expected localStorage keys."""

    def test_chat_history_key(self):
        response = client.get("/")
        assert "classgen_chat_history" in response.text

    def test_thread_id_key(self):
        response = client.get("/")
        assert "classgen_thread_id" in response.text


class TestNativeNotificationGuard:
    """Native notification is guarded by permission check."""

    def test_permission_check(self):
        response = client.get("/")
        html = response.text
        assert "Notification.permission" in html
        assert "'granted'" in html


class TestConfigEndpointStillWorks:
    """GET /api/config is used by frontend for notification decisions."""

    def test_config_returns_200(self):
        response = client.get("/api/config")
        assert response.status_code == 200

    def test_config_has_expected_keys(self):
        data = client.get("/api/config").json()
        assert "sse_streaming" in data
        assert "structured_output" in data
