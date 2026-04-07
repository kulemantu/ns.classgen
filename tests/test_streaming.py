"""Tests for SSE streaming endpoint and JSONBlockAccumulator."""

import json
import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.api.chat import JSONBlockAccumulator
from tests.fixtures import SAMPLE_LESSON_JSON, SAMPLE_LESSON_JSON_DICT

client = TestClient(app)

SAMPLE_BLOCKS = SAMPLE_LESSON_JSON_DICT["blocks"]


# ---------------------------------------------------------------------------
# JSONBlockAccumulator unit tests
# ---------------------------------------------------------------------------


class TestJSONBlockAccumulator:
    def test_single_block(self):
        acc = JSONBlockAccumulator()
        block_json = json.dumps({"type": "opener", "title": "Test", "body": "X"})
        text = f'{{"version":"4.0","blocks":[{block_json}]}}'
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 1
        assert completed[0]["type"] == "opener"

    def test_multiple_blocks(self):
        acc = JSONBlockAccumulator()
        blocks = [
            {"type": "opener", "title": "A", "body": "B"},
            {"type": "explain", "title": "C", "body": "D"},
        ]
        text = json.dumps({"version": "4.0", "blocks": blocks})
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 2
        assert completed[0]["type"] == "opener"
        assert completed[1]["type"] == "explain"

    def test_partial_block_not_emitted(self):
        acc = JSONBlockAccumulator()
        text = '{"version":"4.0","blocks":[{"type":"opener","title":"T'
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 0

    def test_full_lesson_json(self):
        acc = JSONBlockAccumulator()
        completed = []
        for ch in SAMPLE_LESSON_JSON:
            completed.extend(acc.feed(ch))
        assert len(completed) == 5
        assert completed[0]["type"] == "opener"
        assert completed[4]["type"] == "teacher_notes"

    def test_blocks_emitted_list_tracks(self):
        acc = JSONBlockAccumulator()
        text = json.dumps({
            "blocks": [{"type": "opener", "title": "A", "body": "B"}]
        })
        for ch in text:
            acc.feed(ch)
        assert len(acc.blocks_emitted) == 1

    def test_nested_braces_in_body(self):
        """Nested JSON-like content in body doesn't confuse depth tracking."""
        acc = JSONBlockAccumulator()
        block = {
            "type": "explain",
            "title": "T",
            "body": 'The equation is {x: 1, y: 2}',
        }
        text = json.dumps({"blocks": [block]})
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 1
        assert completed[0]["body"] == 'The equation is {x: 1, y: 2}'

    def test_buffer_trimmed_between_blocks(self):
        """Buffer is trimmed after each block to limit memory usage."""
        acc = JSONBlockAccumulator()
        blocks = [
            {"type": "opener", "title": "A", "body": "B" * 1000},
            {"type": "explain", "title": "C", "body": "D" * 1000},
        ]
        text = json.dumps({"blocks": blocks})
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 2
        # Buffer should be much smaller than full text after trimming
        assert len(acc.buffer) < len(text)

    def test_malformed_block_json_skipped(self):
        """Block-like structure that isn't valid JSON is skipped."""
        acc = JSONBlockAccumulator()
        # Manually construct text where a brace pair doesn't form valid JSON
        text = '{"blocks": [{invalid json here}]}'
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 0

    def test_block_without_type_field_skipped(self):
        """A valid JSON object without 'type' key is not emitted."""
        acc = JSONBlockAccumulator()
        text = json.dumps({"blocks": [{"title": "A", "body": "B"}]})
        completed = []
        for ch in text:
            completed.extend(acc.feed(ch))
        assert len(completed) == 0


# ---------------------------------------------------------------------------
# _sse_event and _has_content helpers
# ---------------------------------------------------------------------------


class TestSSEEvent:
    def test_basic_event(self):
        from classgen.api.chat import _sse_event
        result = _sse_event("block", {"type": "opener"})
        assert result.startswith("event: block\n")
        assert "data: " in result
        assert result.endswith("\n\n")

    def test_event_name_newline_sanitized(self):
        from classgen.api.chat import _sse_event
        result = _sse_event("block\nevil: inject", {"ok": True})
        assert "\nevil:" not in result
        assert result.startswith("event: blockevil: inject\n")

    def test_string_data_json_serialized(self):
        from classgen.api.chat import _sse_event
        result = _sse_event("fallback", "raw text with\nnewlines")
        # String data should be JSON-serialized (quoted)
        assert '"raw text with\\nnewlines"' in result


class TestHasContent:
    def test_blocks_in_text_no_pack(self):
        from classgen.api.chat import _has_content
        assert _has_content("[BLOCK_START_OPENER] test", None) is True

    def test_no_blocks_no_pack(self):
        from classgen.api.chat import _has_content
        assert _has_content("Just a question", None) is False

    def test_no_blocks_with_pack(self):
        from classgen.api.chat import _has_content
        from classgen.core.models import LessonPack, OpenerBlock
        pack = LessonPack(blocks=[OpenerBlock(title="T", body="B")])
        assert _has_content("no markers here", pack) is True

    def test_no_blocks_empty_pack(self):
        from classgen.api.chat import _has_content
        from classgen.core.models import LessonPack
        pack = LessonPack(blocks=[])
        assert _has_content("no markers", pack) is False


# ---------------------------------------------------------------------------
# Config endpoint
# ---------------------------------------------------------------------------


class TestConfigEndpoint:
    def test_config_returns_flags(self):
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "sse_streaming" in data
        assert "structured_output" in data

    def test_config_defaults_off(self):
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/api/config")
            data = response.json()
            assert data["sse_streaming"] is False
            assert data["structured_output"] is False

    def test_config_sse_false_when_structured_off(self):
        """SSE reports false when structured_output prerequisite is off."""
        with patch.dict(os.environ, {
            "FF_SSE_STREAMING": "true",
            "FF_STRUCTURED_OUTPUT": "false",
        }, clear=True):
            response = client.get("/api/config")
            data = response.json()
            assert data["sse_streaming"] is False
            assert data["structured_output"] is False

    def test_config_sse_true_when_both_on(self):
        """SSE reports true only when both SSE and structured_output are on."""
        with patch.dict(os.environ, {
            "FF_SSE_STREAMING": "true",
            "FF_STRUCTURED_OUTPUT": "true",
        }, clear=True):
            response = client.get("/api/config")
            data = response.json()
            assert data["sse_streaming"] is True
            assert data["structured_output"] is True

    def test_config_does_not_leak_internal_flags(self):
        """Only client-safe flags are exposed, not internal ones."""
        with patch.dict(os.environ, {
            "FF_STRUCTURED_OUTPUT": "true",
            "FF_SSE_STREAMING": "true",
            "FF_JSON_RESPONSE_FORMAT": "true",
            "FF_EMBEDDED_QUIZ": "true",
        }):
            response = client.get("/api/config")
            data = response.json()
            assert set(data.keys()) == {"sse_streaming", "structured_output"}
            assert "json_response_format" not in data
            assert "embedded_quiz" not in data


# ---------------------------------------------------------------------------
# Stream endpoint
# ---------------------------------------------------------------------------


class TestStreamEndpoint:
    def test_stream_flag_off_returns_json(self):
        """When SSE flag is off, stream endpoint returns normal JSON."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock) as mock_llm,
            patch("classgen.api.chat.get_session_history", return_value=[]),
            patch("classgen.api.chat.log_session"),
            patch("classgen.api.chat.generate_pdf_from_markdown", return_value="test.pdf"),
            patch("classgen.api.chat.generate_homework_code", return_value="TEST42"),
            patch("classgen.api.chat.save_homework_code"),
        ):
            mock_llm.return_value = "[BLOCK_START_OPENER]\nTitle: Test\nSummary: S\nDetails: D\n[BLOCK_END]"
            response = client.post(
                "/api/chat/stream",
                json={"message": "SS2 Biology: Test", "thread_id": "t1"},
            )
            assert response.status_code == 200
            # Should be JSON, not SSE
            data = response.json()
            assert "reply" in data

    @patch("classgen.api.chat.save_homework_code")
    @patch("classgen.api.chat.generate_homework_code", return_value="BIO42")
    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="test.pdf")
    @patch("classgen.api.chat.log_session")
    @patch("classgen.api.chat.get_session_history", return_value=[])
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    def test_stream_emits_sse_events(
        self, mock_llm, mock_hist, mock_log, mock_pdf,
        mock_code, mock_save,
    ):
        """When flags are on, stream endpoint returns SSE events."""
        mock_llm.return_value = SAMPLE_LESSON_JSON

        async def mock_stream(*args, **kwargs):
            for ch in SAMPLE_LESSON_JSON:
                yield ch

        with (
            patch.dict(os.environ, {
                "FF_SSE_STREAMING": "true",
                "FF_STRUCTURED_OUTPUT": "true",
            }),
            patch(
                "classgen.api.chat.stream_openrouter",
                side_effect=mock_stream,
            ),
        ):
            response = client.post(
                "/api/chat/stream",
                json={"message": "SS2 Biology: Photosynthesis", "thread_id": "t1"},
            )
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type

            # Parse SSE events
            text = response.text
            events = _parse_sse(text)

            # Should have meta, 5 blocks, and done
            event_types = [e["event"] for e in events]
            assert "meta" in event_types
            assert event_types.count("block") == 5
            assert "done" in event_types


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE text into a list of {event, data} dicts."""
    events = []
    current_event = ""
    current_data = ""
    for line in text.split("\n"):
        if line.startswith("event: "):
            current_event = line[7:]
        elif line.startswith("data: "):
            current_data = line[6:]
        elif line == "" and current_event:
            try:
                data = json.loads(current_data)
            except json.JSONDecodeError:
                data = current_data
            events.append({"event": current_event, "data": data})
            current_event = ""
            current_data = ""
    return events
