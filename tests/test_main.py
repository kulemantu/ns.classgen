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
[BLOCK_END]

[BLOCK_START_HOMEWORK]
Title: Water Detective
Summary: Story problem
Details: You are a water engineer investigating a drought.
[BLOCK_END]"""

SAMPLE_QUIZ = [
    {"question": "What drives the water cycle?", "options": ["A) Wind", "B) Sun", "C) Moon", "D) Gravity"], "correct": 1},
]

@patch("main.save_homework_code")
@patch("main.generate_homework_code", return_value="WATR42")
@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.get_session_history")
@patch("main.generate_pdf_from_markdown")
@patch("main.handle_command", return_value=None)
def test_twilio_webhook_text_input(mock_cmd, mock_generate_pdf, mock_get_history, mock_log, mock_call_openrouter, mock_gen_code, mock_save_code):
    mock_get_history.return_value = []
    # First call returns lesson, second returns quiz JSON
    mock_call_openrouter.side_effect = [SAMPLE_LESSON_RESPONSE, '[{"question":"Q1","options":["A","B","C","D"],"correct":0}]']
    mock_generate_pdf.return_value = "lesson_plan_123.pdf"

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
    assert "WATR42" in content

    assert mock_log.call_count == 2
    mock_generate_pdf.assert_called_once()
    mock_save_code.assert_called_once()


@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.get_session_history")
@patch("main.handle_command", return_value=None)
def test_twilio_webhook_clarifying_question_no_pdf(mock_cmd, mock_get_history, mock_log, mock_call_openrouter):
    """Clarifying questions should NOT generate a PDF or homework code."""
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
    assert "<Media>" not in content

def test_twilio_webhook_voice_note():
    """Voice notes should be rejected gracefully without calling the LLM."""
    form_data = {
        "From": "whatsapp:+0987654321",
        "Body": "",
        "MediaUrl0": "https://api.twilio.com/audio.ogg",
        "MediaContentType0": "audio/ogg"
    }

    response = client.post("/webhook/twilio", data=form_data)

    assert response.status_code == 200
    content = response.text
    assert "Voice notes" in content
    assert "supported yet" in content

def test_twilio_webhook_empty_input():
    form_data = {
        "From": "whatsapp:+0987654321",
        "Body": "",
    }

    response = client.post("/webhook/twilio", data=form_data)

    assert response.status_code == 200
    content = response.text
    assert "Welcome to ClassGen" in content


# --- Homework Code Endpoint Tests ---

@patch("main.get_homework_code")
def test_homework_page_not_found(mock_get_hw):
    mock_get_hw.return_value = None
    response = client.get("/h/BADCODE")
    assert response.status_code == 404

@patch("main.get_homework_code")
def test_homework_data_not_found(mock_get_hw):
    mock_get_hw.return_value = None
    response = client.get("/api/h/BADCODE")
    assert response.status_code == 404

@patch("main.get_homework_code")
def test_homework_data_found(mock_get_hw):
    mock_get_hw.return_value = {
        "code": "MATH42",
        "homework_block": "Do the homework",
        "quiz_questions": SAMPLE_QUIZ,
    }
    response = client.get("/api/h/MATH42")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "MATH42"
    assert len(data["quiz_questions"]) == 1

@patch("main.save_quiz_submission")
@patch("main.get_homework_code")
def test_submit_quiz(mock_get_hw, mock_save_sub):
    mock_get_hw.return_value = {
        "code": "MATH42",
        "quiz_questions": SAMPLE_QUIZ,
    }
    mock_save_sub.return_value = True

    response = client.post("/h/MATH42/submit", json={
        "student_name": "Amina",
        "student_class": "SS2",
        "answers": [1],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 1
    assert data["total"] == 1
    assert data["results"][0]["is_correct"] is True

@patch("main.save_quiz_submission")
@patch("main.get_homework_code")
def test_submit_quiz_wrong_answer(mock_get_hw, mock_save_sub):
    mock_get_hw.return_value = {
        "code": "MATH42",
        "quiz_questions": SAMPLE_QUIZ,
    }
    mock_save_sub.return_value = True

    response = client.post("/h/MATH42/submit", json={
        "student_name": "Chidi",
        "student_class": "SS2",
        "answers": [0],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0
    assert data["results"][0]["is_correct"] is False
