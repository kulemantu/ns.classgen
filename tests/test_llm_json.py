"""Tests for call_openrouter_json and stream_openrouter in classgen.services.llm."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from classgen.services.llm import (
    call_openrouter_json,
    stream_openrouter,
)


class TestCallOpenrouterJson:
    @pytest.mark.asyncio
    async def test_plain_call_when_flag_off(self):
        """Without FF_JSON_RESPONSE_FORMAT, no response_format kwarg."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"blocks":[]}'))]
        mock_create = AsyncMock(return_value=mock_completion)

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            result = await call_openrouter_json("sys", "user")

        assert result == '{"blocks":[]}'
        call_kwargs = mock_create.call_args
        assert "response_format" not in call_kwargs.kwargs

    @pytest.mark.asyncio
    async def test_response_format_when_flag_on(self):
        """With FF_JSON_RESPONSE_FORMAT, response_format is passed."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{}'))]
        mock_create = AsyncMock(return_value=mock_completion)

        with (
            patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "true"}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            result = await call_openrouter_json("sys", "user")

        assert result == '{}'
        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs.get("response_format") == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_retry_on_response_format_rejection(self):
        """If model rejects response_format, retries without it."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"ok":true}'))]

        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and "response_format" in kwargs:
                raise Exception("response_format is not supported for this model")
            return mock_completion

        with (
            patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "true"}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            result = await call_openrouter_json("sys", "user")

        assert result == '{"ok":true}'
        assert call_count == 2  # first call failed, retry succeeded

    @pytest.mark.asyncio
    async def test_returns_none_on_unrelated_error(self):
        """Non-response_format errors return None (no retry)."""
        async def mock_create(**kwargs):
            raise Exception("connection timeout")

        with (
            patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "true"}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            result = await call_openrouter_json("sys", "user")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_error_without_flag(self):
        """Errors without the flag return None."""
        async def mock_create(**kwargs):
            raise Exception("network error")

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            result = await call_openrouter_json("sys", "user")

        assert result is None


class TestStreamOpenrouter:
    @pytest.mark.asyncio
    async def test_yields_tokens(self):
        """stream_openrouter yields delta content from chunks."""
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
        ]

        async def mock_create(**kwargs):
            for chunk in chunks:
                yield chunk

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = AsyncMock(return_value=mock_create())
            tokens = []
            async for token in stream_openrouter("sys", "user"):
                tokens.append(token)

        assert tokens == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_skips_empty_choices(self):
        """Chunks with empty choices list are skipped."""
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="data"))]),
            MagicMock(choices=[]),  # empty choices (stream end marker)
        ]

        async def mock_create(**kwargs):
            for chunk in chunks:
                yield chunk

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = AsyncMock(return_value=mock_create())
            tokens = []
            async for token in stream_openrouter("sys", "user"):
                tokens.append(token)

        assert tokens == ["data"]

    @pytest.mark.asyncio
    async def test_skips_none_delta(self):
        """Chunks with None delta content are skipped."""
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="a"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="b"))]),
        ]

        async def mock_create(**kwargs):
            for chunk in chunks:
                yield chunk

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = AsyncMock(return_value=mock_create())
            tokens = []
            async for token in stream_openrouter("sys", "user"):
                tokens.append(token)

        assert tokens == ["a", "b"]

    @pytest.mark.asyncio
    async def test_error_stops_gracefully(self):
        """Exception during streaming stops the generator without crashing."""
        async def mock_create(**kwargs):
            raise Exception("stream error")

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            tokens = []
            async for token in stream_openrouter("sys", "user"):
                tokens.append(token)

        assert tokens == []

    @pytest.mark.asyncio
    async def test_retry_on_response_format_rejection(self):
        """Streaming retries without response_format if model rejects it."""
        good_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="ok"))]),
        ]

        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and "response_format" in kwargs:
                raise Exception("response_format not supported for streaming")

            async def gen():
                for chunk in good_chunks:
                    yield chunk

            return gen()

        with (
            patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "true"}, clear=True),
            patch("classgen.services.llm.openrouter_client") as mock_client,
        ):
            mock_client.chat.completions.create = mock_create
            tokens = []
            async for token in stream_openrouter("sys", "user"):
                tokens.append(token)

        assert tokens == ["ok"]
        assert call_count == 2
