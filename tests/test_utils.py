"""Unit tests for LLM client and data layer functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openai import APIConnectionError, AuthenticationError

from classgen.data.sessions import get_session_history, log_session
from classgen.services.llm import call_openrouter


def _mock_completion(content: str = "ok"):
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def _api_connection_error() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "https://openrouter.ai/x"))


def _auth_error() -> AuthenticationError:
    req = httpx.Request("POST", "https://openrouter.ai/x")
    return AuthenticationError(
        message="User not found.",
        response=httpx.Response(401, request=req),
        body=None,
    )


@pytest.mark.asyncio
async def test_call_openrouter_success():
    with patch(
        "classgen.services.llm.openrouter_client.chat.completions.create", new_callable=AsyncMock
    ) as mock_create:
        mock_message = MagicMock()
        mock_message.content = "Test Plan A and Plan B"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        response = await call_openrouter("sys prompt", "user prompt")
        assert response == "Test Plan A and Plan B"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_call_openrouter_failure():
    with patch(
        "classgen.services.llm.openrouter_client.chat.completions.create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.side_effect = Exception("API Down")
        response = await call_openrouter("sys prompt", "user prompt")
        assert response is None
        # Generic Exception is not classified as retryable -> single attempt.
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_call_openrouter_retries_once_on_transient_error():
    """Transient APIConnectionError on attempt 1 -> retry succeeds on attempt 2."""
    with (
        patch(
            "classgen.services.llm.openrouter_client.chat.completions.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch("classgen.services.llm.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_create.side_effect = [_api_connection_error(), _mock_completion("recovered")]
        response = await call_openrouter("sys", "user")
        assert response == "recovered"
        assert mock_create.call_count == 2


@pytest.mark.asyncio
async def test_call_openrouter_no_retry_on_auth_error():
    """AuthenticationError (401) is permanent — must NOT retry."""
    with (
        patch(
            "classgen.services.llm.openrouter_client.chat.completions.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch("classgen.services.llm.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_create.side_effect = _auth_error()
        response = await call_openrouter("sys", "user")
        assert response is None
        assert mock_create.call_count == 1
        mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_call_openrouter_returns_none_after_two_transient_failures():
    """Both attempts hit transient errors — return None, do not raise."""
    with (
        patch(
            "classgen.services.llm.openrouter_client.chat.completions.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch("classgen.services.llm.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_create.side_effect = [_api_connection_error(), _api_connection_error()]
        response = await call_openrouter("sys", "user")
        assert response is None
        assert mock_create.call_count == 2


def test_log_session_no_supabase():
    with patch("classgen.data.sessions.supabase", None):
        result = log_session("thread_1", "user", "hello")
        assert result is None


def test_get_session_history_no_supabase():
    with patch("classgen.data.sessions.supabase", None):
        result = get_session_history("thread_1")
        assert isinstance(result, list)


def test_log_session_with_supabase():
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value.data = "mock_data"
    mock_insert.return_value.execute = mock_execute
    mock_table.return_value.insert = mock_insert
    mock_supabase.table = mock_table

    with patch("classgen.data.sessions.supabase", mock_supabase):
        log_session("thread_1", "user", "hello")
        mock_supabase.table.assert_called_with("sessions")
