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
@patch("main.log_usage")
@patch("main.check_usage")
def test_twilio_webhook_text_input(mock_check, mock_log_usage, mock_cmd, mock_generate_pdf, mock_get_history, mock_log, mock_call_openrouter, mock_gen_code, mock_save_code):
    mock_check.return_value = type("U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""})()
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
@patch("main.log_usage")
@patch("main.check_usage")
def test_twilio_webhook_clarifying_question_no_pdf(mock_check, mock_log_usage, mock_cmd, mock_get_history, mock_log, mock_call_openrouter):
    mock_check.return_value = type("U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""})()
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


# --- Web Teacher Profile API Tests ---

@patch("main.get_teacher_by_phone")
def test_teacher_profile_unregistered(mock_get):
    mock_get.return_value = None
    response = client.get("/api/teacher/profile?thread_id=chat_test123")
    assert response.status_code == 200
    data = response.json()
    assert data["registered"] is False


@patch("main.list_homework_codes_for_teacher", return_value=[])
@patch("main.get_teacher_lesson_stats", return_value={"total": 5, "this_week": 2, "this_month": 3})
@patch("main.get_teacher_by_phone")
def test_teacher_profile_registered(mock_get, mock_stats, mock_codes):
    mock_get.return_value = {"name": "Mrs. Test", "slug": "mrs-test", "classes": ["SS2 Biology"]}
    response = client.get("/api/teacher/profile?thread_id=chat_test123")
    assert response.status_code == 200
    data = response.json()
    assert data["registered"] is True
    assert data["teacher"]["name"] == "Mrs. Test"
    assert data["stats"]["total"] == 5
    assert data["codes"] == []


@patch("main.save_teacher")
def test_teacher_register(mock_save):
    mock_save.return_value = {"name": "Mrs. Okafor", "slug": "mrs-okafor", "classes": []}
    response = client.post("/api/teacher/register", json={
        "thread_id": "chat_abc123",
        "name": "Mrs. Okafor",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["registered"] is True
    assert data["teacher"]["name"] == "Mrs. Okafor"
    mock_save.assert_called_once_with("chat_abc123", "Mrs. Okafor")


def test_teacher_register_short_name():
    response = client.post("/api/teacher/register", json={
        "thread_id": "chat_abc123",
        "name": "X",
    })
    assert response.status_code == 422


@patch("main.update_teacher_name")
def test_teacher_update_name(mock_update):
    mock_update.return_value = {"name": "Mrs. New Name", "slug": "mrs-new-name", "classes": []}
    response = client.patch("/api/teacher/profile", json={
        "thread_id": "chat_abc123",
        "name": "Mrs. New Name",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["teacher"]["name"] == "Mrs. New Name"


@patch("main.get_teacher_by_phone")
@patch("main.add_teacher_class")
def test_teacher_add_class(mock_add, mock_get):
    mock_get.side_effect = [
        {"name": "T", "slug": "t", "classes": []},
        {"name": "T", "slug": "t", "classes": ["SS2 Biology"]},
    ]
    mock_add.return_value = True
    response = client.post("/api/teacher/classes", json={
        "thread_id": "chat_abc123",
        "class_name": "SS2 Biology",
    })
    assert response.status_code == 200
    data = response.json()
    assert "SS2 Biology" in data["classes"]


@patch("main.get_teacher_by_phone")
@patch("main.remove_teacher_class")
def test_teacher_remove_class(mock_remove, mock_get):
    mock_get.side_effect = [
        {"name": "T", "slug": "t", "classes": ["SS2 Biology"]},
        {"name": "T", "slug": "t", "classes": []},
    ]
    mock_remove.return_value = True
    response = client.delete("/api/teacher/classes/SS2%20Biology?thread_id=chat_abc123")
    assert response.status_code == 200
    data = response.json()
    assert data["classes"] == []


@patch("main.clear_session_history")
def test_clear_history(mock_clear):
    mock_clear.return_value = True
    response = client.delete("/api/teacher/history?thread_id=chat_abc123")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_clear.assert_called_once_with("chat_abc123")


@patch("main.save_homework_code")
@patch("main.generate_homework_code", return_value="WEB001")
@patch("main.call_openrouter", new_callable=AsyncMock)
@patch("main.log_session")
@patch("main.get_session_history")
@patch("main.generate_pdf_from_markdown")
@patch("main.handle_command", return_value=None)
@patch("main.log_usage")
@patch("main.check_usage")
@patch("main.get_teacher_by_phone")
def test_chat_with_registered_teacher(mock_get_teacher, mock_check, mock_log_usage,
                                       mock_cmd, mock_pdf,
                                       mock_history, mock_log, mock_llm,
                                       mock_gen_code, mock_save_code):
    """When a registered web teacher chats, usage is checked and teacher_phone is set."""
    mock_get_teacher.return_value = {"name": "Mrs. Web", "slug": "mrs-web", "classes": []}
    mock_check.return_value = type("U", (), {"allowed": True, "remaining": 4, "tier": "free", "message": ""})()
    mock_history.return_value = []
    mock_llm.side_effect = [SAMPLE_LESSON_RESPONSE, '[]']
    mock_pdf.return_value = "lesson_plan_web.pdf"

    response = client.post("/api/chat", json={
        "message": "SS2 Biology: Photosynthesis",
        "thread_id": "chat_registered",
    })
    assert response.status_code == 200
    # Verify usage was checked and logged
    mock_check.assert_called_once_with("chat_registered")
    mock_log_usage.assert_called_once_with("chat_registered", "lesson")
    # Verify save_homework_code was called with teacher_phone=threadId
    mock_save_code.assert_called_once()
    call_kwargs = mock_save_code.call_args
    assert call_kwargs[1].get("teacher_phone") == "chat_registered" or \
           (len(call_kwargs[0]) >= 6 and call_kwargs[0][5] == "chat_registered")
