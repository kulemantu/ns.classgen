import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "ClassGen" in response.text

SAMPLE_LESSON_RESPONSE = """[BLOCK_START_HOOK]
Title: The Water Cycle in Your Kitchen
Summary: You see the water cycle every time you boil water!
Details: Start by boiling a kettle and holding a cold plate above the steam.
[BLOCK_END]

[BLOCK_START_FACT]
Title: Earth Has the Same Water as the Dinosaurs
Summary: Every drop of water on Earth has been recycled for billions of years.
Details: The water cycle means no new water is created — it just moves around.
[BLOCK_END]"""

@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.get_session_history")
@patch("main.generate_pdf_from_markdown")
def test_twilio_webhook_text_input(mock_generate_pdf, mock_get_history, mock_log, mock_call_openrouter):
    # Setup mocks
    mock_get_history.return_value = []
    mock_call_openrouter.return_value = SAMPLE_LESSON_RESPONSE
    mock_generate_pdf.return_value = "lesson_plan_123.pdf"

    # Simulate Twilio form data
    form_data = {
        "From": "whatsapp:+1234567890",
        "Body": "I need a math lesson",
    }

    response = client.post("/webhook/twilio", data=form_data)

    assert response.status_code == 200
    content = response.text
    assert "Water Cycle" in content
    assert "<Message>" in content
    assert "<Media>" in content
    assert "lesson_plan_123.pdf" in content

    # Verify our mocks were called
    assert mock_log.call_count == 2 # 1 for user, 1 for assistant
    mock_call_openrouter.assert_called_once()
    mock_generate_pdf.assert_called_once()


@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.get_session_history")
def test_twilio_webhook_clarifying_question_no_pdf(mock_get_history, mock_log, mock_call_openrouter):
    """Clarifying questions should NOT generate a PDF."""
    mock_get_history.return_value = []
    mock_call_openrouter.return_value = "What grade level are we working with?\nSUGGESTIONS: [SS1] | [SS2] | [SS3]"

    form_data = {
        "From": "whatsapp:+1234567890",
        "Body": "math",
    }

    response = client.post("/webhook/twilio", data=form_data)

    assert response.status_code == 200
    content = response.text
    assert "What grade level" in content
    assert "<Media>" not in content  # No PDF for clarifying questions

@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.generate_pdf_from_markdown")
def test_twilio_webhook_voice_note(mock_generate_pdf, mock_log, mock_call_openrouter):
    mock_call_openrouter.return_value = "Here is the audio interpreted Plan A and Plan B"
    mock_generate_pdf.return_value = "lesson_plan_audio.pdf"
    
    form_data = {
        "From": "whatsapp:+0987654321",
        "Body": "",
        "MediaUrl0": "https://api.twilio.com/audio.ogg",
        "MediaContentType0": "audio/ogg"
    }
    
    response = client.post("/webhook/twilio", data=form_data)
    
    assert response.status_code == 200
    content = response.text
    assert "Here is the audio interpreted" in content
    
    # Ensure our dummy transcription filler kicked in
    # The first call to log_session should contain the transcription placeholder
    call_args = mock_log.call_args_list[0]
    assert "Voice Note Transcription Placeholder" in call_args[0][2]

def test_twilio_webhook_empty_input():
    form_data = {
        "From": "whatsapp:+0987654321",
        "Body": "",
    }
    
    response = client.post("/webhook/twilio", data=form_data)
    
    assert response.status_code == 200
    content = response.text
    assert "Welcome to ClassGen" in content
