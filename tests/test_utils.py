"""Unit tests for LLM client and data layer functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from classgen.data.sessions import get_session_history, log_session
from classgen.services.llm import call_openrouter


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
        mock_create.assert_called_once()


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
