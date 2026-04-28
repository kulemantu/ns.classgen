"""Tests for frontend notification and persistence features.

Validates that:
- The Notifications button was removed from the header HTML
- Push toggle remains in the settings sidebar HTML
- Toast element exists in the served HTML
- /api/config still works (used by frontend to decide notification strategy)
- Chat history localStorage keys are referenced in the JS
- The renderAiResponse / restoreConversation / notifyLesson functions exist
"""

import re
from functools import lru_cache

from fastapi.testclient import TestClient

from classgen.api.app import app

client = TestClient(app)


@lru_cache(maxsize=1)
def _served():
    """HTML shell + linked CSS bundle + linked JS bundle, as effectively
    served to the browser. After the V4.1 asset-extraction refactor, content
    that used to be inline in index.html now lives in /assets/app.<hash>.{css,js}."""
    html = client.get("/").text
    css_match = re.search(r"/assets/app\.[a-f0-9]{8}\.css", html)
    js_match = re.search(r"/assets/app\.[a-f0-9]{8}\.js", html)
    assert css_match and js_match, "asset URLs missing from HTML"
    return (
        html
        + "\n"
        + client.get(css_match.group()).text
        + "\n"
        + client.get(js_match.group()).text
    )


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
        served = _served()
        assert "push-toggle" in served
        assert "Push notifications" in served
        assert "togglePush()" in served


class TestToastElement:
    """Toast notification element and styles are present."""

    def test_toast_div_exists(self):
        # The toast <div> itself stays in the HTML body.
        assert 'id="toast"' in client.get("/").text

    def test_toast_dark_background(self):
        """Toast uses dark slate background, not green."""
        assert "#1e293b" in _served()

    def test_toast_dark_mode_variant(self):
        assert '[data-theme="dark"] .toast' in _served()

    def test_toast_high_z_index(self):
        assert "z-index: 9999" in _served()


class TestFrontendFunctions:
    """Key JS functions exist in the served bundle."""

    def test_show_toast(self):
        assert "function showToast(" in _served()

    def test_notify_lesson(self):
        assert "function notifyLesson(" in _served()

    def test_render_ai_response(self):
        assert "function renderAiResponse(" in _served()

    def test_save_conversation(self):
        assert "function saveConversation(" in _served()

    def test_restore_conversation(self):
        assert "function restoreConversation(" in _served()

    def test_humanize(self):
        assert "function humanize(" in _served()

    def test_format_details(self):
        assert "function formatDetails(" in _served()


class TestLocalStorageKeys:
    """The JS references the expected localStorage keys."""

    def test_chat_history_key(self):
        assert "classgen_chat_history" in _served()

    def test_thread_id_key(self):
        assert "classgen_thread_id" in _served()


class TestNativeNotificationGuard:
    """Native notification is guarded by permission check."""

    def test_permission_check(self):
        served = _served()
        assert "Notification.permission" in served
        assert "'granted'" in served


class TestConfigEndpointStillWorks:
    """GET /api/config is used by frontend for notification decisions."""

    def test_config_returns_200(self):
        response = client.get("/api/config")
        assert response.status_code == 200

    def test_config_has_expected_keys(self):
        data = client.get("/api/config").json()
        assert "sse_streaming" in data
        assert "structured_output" in data
