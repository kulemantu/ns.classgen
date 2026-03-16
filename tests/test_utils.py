from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import utils
import db


@pytest.mark.asyncio
async def test_call_openrouter_success():
    with patch('utils.openrouter_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_message = MagicMock()
        mock_message.content = "Test Plan A and Plan B"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        response = await utils.call_openrouter("sys prompt", "user prompt")

        assert response == "Test Plan A and Plan B"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_call_openrouter_failure():
    with patch('utils.openrouter_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API Down")

        response = await utils.call_openrouter("sys prompt", "user prompt")

        assert response is None
        mock_create.assert_called_once()


def test_log_session_no_supabase():
    with patch('db.supabase', None):
        result = db.log_session("thread_1", "user", "hello")
        assert result is None


def test_get_session_history_no_supabase():
    with patch('db.supabase', None):
        result = db.get_session_history("thread_1")
        # In-memory store may have entries from other tests, but should not error
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

    with patch('db.supabase', mock_supabase):
        db.log_session("thread_1", "user", "hello")
        mock_supabase.table.assert_called_with("sessions")
