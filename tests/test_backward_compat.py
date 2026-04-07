"""Backward compatibility tests — verify all behavior is unchanged when flags are off."""

import json
import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.data.homework import _mem_homework, save_homework_code
from classgen.data.lessons import (
    _mem_content_cache,
    cache_lesson,
    get_cached_lesson,
    get_cached_lesson_json,
)
from tests.fixtures import (
    SAMPLE_LESSON_BLOCKS,
    SAMPLE_LESSON_JSON,
    SAMPLE_LESSON_JSON_DICT,
)

client = TestClient(app)


class TestChatEndpointUnchanged:
    """POST /api/chat response shape is identical when all flags are off."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="TEST42")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="test.pdf")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    def test_response_shape(
        self, mock_log, mock_hist, mock_pdf, mock_llm, mock_code, mock_save,
    ):
        mock_llm.side_effect = [
            SAMPLE_LESSON_BLOCKS,
            '[{"question":"Q","options":["A","B","C","D"],"correct":0}]',
        ]
        with patch.dict(os.environ, {}, clear=True):
            response = client.post(
                "/api/chat",
                json={"message": "SS2 Biology: Photosynthesis", "thread_id": "t1"},
            )
        assert response.status_code == 200
        data = response.json()
        # Must have exactly these keys (no lesson_pack when flags off)
        assert set(data.keys()) == {"reply", "pdf_url", "homework_code"}
        assert "BLOCK_START" in data["reply"]
        assert data["pdf_url"] == "/static/test.pdf"
        assert data["homework_code"] == "TEST42"
        # generate_pdf_from_markdown was called (not PDFAdapter)
        mock_pdf.assert_called_once()


class TestWebhookUnchanged:
    """POST /webhook/twilio TwiML is unchanged when all flags are off."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    @patch("classgen.api.webhook.check_usage")
    @patch("classgen.api.webhook.log_usage")
    @patch("classgen.api.webhook.handle_command", return_value=None)
    @patch("classgen.api.chat.generate_pdf_from_markdown")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_homework_code", return_value="BIO42")
    @patch("classgen.api.chat.save_homework_code")
    def test_twiml_shape(
        self, mock_save, mock_code, mock_llm, mock_log, mock_hist,
        mock_pdf, mock_cmd, mock_usage_log, mock_check,
    ):
        mock_check.return_value = type(
            "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
        )()
        mock_llm.side_effect = [
            SAMPLE_LESSON_BLOCKS,
            '[{"question":"Q","options":["A","B","C","D"],"correct":0}]',
        ]
        mock_pdf.return_value = "test.pdf"

        with patch.dict(os.environ, {}, clear=True):
            response = client.post(
                "/webhook/twilio",
                data={"From": "whatsapp:+1234567890", "Body": "SS2 Bio: Photo"},
            )
        assert response.status_code == 200
        assert "<Message>" in response.text
        # PDF mock was called (not adapter)
        mock_pdf.assert_called_once()


class TestOldHomeworkCodesStillWork:
    """Homework codes stored without lesson_json still serve correctly."""

    def setup_method(self):
        _mem_homework.clear()

    def teardown_method(self):
        _mem_homework.clear()

    def test_old_format_serves(self):
        save_homework_code(
            "OLD42", "thread1", SAMPLE_LESSON_BLOCKS,
            [{"question": "Q", "options": ["A", "B", "C", "D"], "correct": 0}],
            "Title: Test\nDetails: Test homework",
        )
        response = client.get("/api/h/OLD42")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "OLD42"
        assert "homework_block" in data
        # No homework_structured when lesson_json is absent
        assert "homework_structured" not in data

    def test_new_format_includes_structured(self):
        save_homework_code(
            "NEW42", "thread1", "raw text",
            [{"question": "Q", "options": ["A", "B", "C", "D"], "correct": 0}],
            "Title: Test\nDetails: Test homework",
            lesson_json=SAMPLE_LESSON_JSON_DICT,
        )
        response = client.get("/api/h/NEW42")
        assert response.status_code == 200
        data = response.json()
        assert "homework_structured" in data
        assert data["homework_structured"]["title"] == "The Oxygen Detective"


class TestOldLessonCacheStillWorks:
    """Cached lessons without lesson_json still return content."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    def test_old_cache_returns_content(self):
        cache_lesson("Biology", "Photosynthesis", "SS2", SAMPLE_LESSON_BLOCKS)
        result = get_cached_lesson("Biology", "Photosynthesis", "SS2")
        assert result is not None
        assert "BLOCK_START" in result

    def test_new_cache_returns_content(self):
        cache_lesson(
            "Biology", "Photosynthesis", "SS2",
            json.dumps(SAMPLE_LESSON_JSON_DICT),
            lesson_json=SAMPLE_LESSON_JSON_DICT,
        )
        result = get_cached_lesson("Biology", "Photosynthesis", "SS2")
        assert result is not None


class TestGetCachedLessonJson:
    """Tests for get_cached_lesson_json — the new JSON cache path."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    def test_returns_json_when_available(self):
        cache_lesson(
            "Biology", "Photo", "SS2", "raw text",
            lesson_json=SAMPLE_LESSON_JSON_DICT,
        )
        result = get_cached_lesson_json("Biology", "Photo", "SS2")
        assert result is not None
        assert result["version"] == "4.0"
        assert len(result["blocks"]) == 5

    def test_returns_none_when_no_json(self):
        cache_lesson("Biology", "Photo", "SS2", "raw text only")
        result = get_cached_lesson_json("Biology", "Photo", "SS2")
        assert result is None

    def test_returns_none_for_miss(self):
        result = get_cached_lesson_json("Physics", "Gravity", "SS1")
        assert result is None


class TestHomeworkStructuredEdgeCases:
    """Edge cases for the homework_structured field in /api/h/{code}."""

    def setup_method(self):
        _mem_homework.clear()

    def teardown_method(self):
        _mem_homework.clear()

    def test_lesson_json_without_homework_block(self):
        """lesson_json exists but has no homework block → no homework_structured."""
        lesson_json = {
            "blocks": [
                {"type": "opener", "title": "T", "body": "B"},
            ]
        }
        save_homework_code(
            "NH42", "t1", "raw", [], "hw text",
            lesson_json=lesson_json,
        )
        response = client.get("/api/h/NH42")
        data = response.json()
        assert "homework_structured" not in data

    def test_lesson_json_empty_dict(self):
        """lesson_json is {} → no homework_structured."""
        save_homework_code("ED42", "t1", "raw", [], "hw text", lesson_json={})
        response = client.get("/api/h/ED42")
        data = response.json()
        assert "homework_structured" not in data

    def test_homework_structured_fields_are_strings(self):
        """Structured fields are coerced to strings for safety."""
        save_homework_code(
            "SF42", "t1", "raw", [], "hw text",
            lesson_json=SAMPLE_LESSON_JSON_DICT,
        )
        response = client.get("/api/h/SF42")
        data = response.json()
        hw = data["homework_structured"]
        assert isinstance(hw["title"], str)
        assert isinstance(hw["narrative"], str)
        assert isinstance(hw["format"], str)
        assert isinstance(hw["completion"], str)
        assert isinstance(hw["tasks"], list)

    def test_homework_structured_no_assessment_tip_leaked(self):
        """assessment_tip (teacher-only) is NOT included in student response."""
        save_homework_code(
            "AT42", "t1", "raw", [], "hw text",
            lesson_json=SAMPLE_LESSON_JSON_DICT,
        )
        response = client.get("/api/h/AT42")
        data = response.json()
        hw = data["homework_structured"]
        assert "assessment_tip" not in hw
        assert "quiz" not in hw
        assert "expected_answers" not in hw


class TestFlagsOnIntegration:
    """Tests that exercise the flags-ON code paths end-to-end."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="JSON42")
    @patch("classgen.api.chat.call_openrouter_json", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="test.pdf")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    def test_structured_output_returns_lesson_pack(
        self, mock_log, mock_hist, mock_pdf, mock_llm, mock_code, mock_save,
    ):
        """With FF_STRUCTURED_OUTPUT=true, response includes lesson_pack."""
        mock_llm.return_value = SAMPLE_LESSON_JSON
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True):
            response = client.post(
                "/api/chat",
                json={"message": "SS2 Biology: Photosynthesis", "thread_id": "t1"},
            )
        data = response.json()
        assert "lesson_pack" in data
        assert data["lesson_pack"]["version"] == "4.0"
        assert len(data["lesson_pack"]["blocks"]) == 5

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="EMB42")
    @patch("classgen.api.chat.call_openrouter_json", new_callable=AsyncMock)
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    def test_embedded_quiz_skips_second_llm_call(
        self, mock_log, mock_hist, mock_llm, mock_code, mock_save,
    ):
        """With FF_EMBEDDED_QUIZ + FF_STRUCTURED_OUTPUT, quiz from JSON, no second call."""
        mock_llm.return_value = SAMPLE_LESSON_JSON
        with patch.dict(os.environ, {
            "FF_STRUCTURED_OUTPUT": "true",
            "FF_EMBEDDED_QUIZ": "true",
        }, clear=True):
            # Patch PDFAdapter to avoid file I/O
            with patch("classgen.api.chat.PDFAdapter") as mock_adapter_cls:
                mock_adapter_cls.return_value.render_lesson.return_value = "test.pdf"
                client.post(
                    "/api/chat",
                    json={"message": "SS2 Biology: Photosynthesis", "thread_id": "t1"},
                )
        # call_openrouter_json should be called only ONCE (lesson, not quiz)
        assert mock_llm.call_count == 1
        # save_homework_code should still be called with quiz data
        mock_save.assert_called_once()
        saved_quiz = mock_save.call_args[0][3]  # 4th positional arg = quiz_questions
        assert len(saved_quiz) == 5

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="PDF42")
    @patch("classgen.api.chat.call_openrouter_json", new_callable=AsyncMock)
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    def test_pdf_adapter_used_when_structured(
        self, mock_log, mock_hist, mock_llm, mock_code, mock_save,
    ):
        """With FF_STRUCTURED_OUTPUT, PDFAdapter is used instead of generate_pdf_from_markdown."""
        mock_llm.return_value = SAMPLE_LESSON_JSON
        with (
            patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True),
            patch("classgen.api.chat.PDFAdapter") as mock_adapter_cls,
        ):
            mock_adapter_cls.return_value.render_lesson.return_value = "test.pdf"
            response = client.post(
                "/api/chat",
                json={"message": "SS2 Biology: Photo", "thread_id": "t1"},
            )
        data = response.json()
        assert data["pdf_url"] == "/static/test.pdf"
        mock_adapter_cls.return_value.render_lesson.assert_called_once()


class TestQuizGenerationStillCalled:
    """Second LLM call for quiz fires when embedded_quiz flag is off."""

    def setup_method(self):
        _mem_content_cache.clear()

    def teardown_method(self):
        _mem_content_cache.clear()

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="QZ42")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="test.pdf")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.log_session")
    def test_second_llm_call_fires(
        self, mock_log, mock_hist, mock_pdf, mock_llm, mock_code, mock_save,
    ):
        mock_llm.side_effect = [
            SAMPLE_LESSON_BLOCKS,
            '[{"question":"Q","options":["A","B","C","D"],"correct":0}]',
        ]
        with patch.dict(os.environ, {}, clear=True):
            client.post(
                "/api/chat",
                json={"message": "SS2 Biology: Test", "thread_id": "t1"},
            )
        # call_openrouter should be called twice (lesson + quiz)
        assert mock_llm.call_count == 2
