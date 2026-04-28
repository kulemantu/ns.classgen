"""Integration tests for ClassGen API endpoints.

Tests use the new classgen.* package imports. Patches target the modules
where the functions are actually USED (the api routers), not where they're defined.
"""

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app

client = TestClient(app)

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
    {
        "question": "What drives the water cycle?",
        "options": ["A) Wind", "B) Sun", "C) Moon", "D) Gravity"],
        "correct": 1,
    },
]


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "ClassGen" in response.text


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Twilio Webhook Tests ---


@patch("classgen.api.webhook.check_usage")
@patch("classgen.api.webhook.log_usage")
@patch("classgen.api.webhook.handle_command", return_value=None)
@patch("classgen.api.chat.generate_pdf_from_markdown")
@patch("classgen.api.chat.get_session_history")
@patch("classgen.api.chat.log_session")
@patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
@patch("classgen.api.chat.generate_homework_code", return_value="WATR42")
@patch("classgen.api.chat.save_homework_code")
def test_twilio_webhook_text_input(
    mock_save_code,
    mock_gen_code,
    mock_call_openrouter,
    mock_log,
    mock_get_history,
    mock_generate_pdf,
    mock_cmd,
    mock_log_usage,
    mock_check,
):
    mock_check.return_value = type(
        "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
    )()
    mock_get_history.return_value = []
    mock_call_openrouter.side_effect = [
        SAMPLE_LESSON_RESPONSE,
        '[{"question":"Q1","options":["A","B","C","D"],"correct":0}]',
    ]
    mock_generate_pdf.return_value = "lesson_plan_123.pdf"

    response = client.post(
        "/webhook/twilio", data={"From": "whatsapp:+1234567890", "Body": "I need a math lesson"}
    )

    assert response.status_code == 200
    content = response.text
    assert "Water Cycle" in content
    assert "<Message>" in content
    assert mock_log.call_count == 2
    mock_generate_pdf.assert_called_once()
    mock_save_code.assert_called_once()


@patch("classgen.api.webhook.check_usage")
@patch("classgen.api.webhook.log_usage")
@patch("classgen.api.webhook.handle_command", return_value=None)
@patch("classgen.api.chat.get_session_history")
@patch("classgen.api.chat.log_session")
@patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
def test_twilio_webhook_clarifying_question_no_pdf(
    mock_call_openrouter, mock_log, mock_get_history, mock_cmd, mock_log_usage, mock_check
):
    mock_check.return_value = type(
        "U", (), {"allowed": True, "remaining": 5, "tier": "free", "message": ""}
    )()
    mock_get_history.return_value = []
    mock_call_openrouter.return_value = (
        "What grade level are we working with?\nSUGGESTIONS: [SS1] | [SS2] | [SS3]"
    )

    response = client.post("/webhook/twilio", data={"From": "whatsapp:+1234567890", "Body": "math"})

    assert response.status_code == 200
    content = response.text
    assert "What grade level" in content


def test_twilio_webhook_voice_note():
    response = client.post(
        "/webhook/twilio",
        data={
            "From": "whatsapp:+0987654321",
            "Body": "",
            "MediaUrl0": "https://api.twilio.com/audio.ogg",
            "MediaContentType0": "audio/ogg",
        },
    )
    assert response.status_code == 200
    assert "Voice notes" in response.text


def test_twilio_webhook_empty_input():
    response = client.post("/webhook/twilio", data={"From": "whatsapp:+0987654321", "Body": ""})
    assert response.status_code == 200
    assert "Welcome to ClassGen" in response.text


# --- Homework Code Tests ---


@patch("classgen.api.homework.get_homework_code")
def test_homework_page_not_found(mock_get_hw):
    mock_get_hw.return_value = None
    response = client.get("/h/BADCODE")
    assert response.status_code == 404


@patch("classgen.api.homework.get_homework_code")
def test_homework_data_not_found(mock_get_hw):
    mock_get_hw.return_value = None
    response = client.get("/api/h/BADCODE")
    assert response.status_code == 404


@patch("classgen.api.homework.get_homework_code")
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


@patch("classgen.api.homework.save_quiz_submission")
@patch("classgen.api.homework.get_homework_code")
def test_submit_quiz(mock_get_hw, mock_save_sub):
    mock_get_hw.return_value = {"code": "MATH42", "quiz_questions": SAMPLE_QUIZ}
    mock_save_sub.return_value = True
    response = client.post(
        "/h/MATH42/submit",
        json={
            "student_name": "Amina",
            "student_class": "SS2",
            "answers": [1],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 1
    assert data["results"][0]["is_correct"] is True


@patch("classgen.api.homework.save_quiz_submission")
@patch("classgen.api.homework.get_homework_code")
def test_submit_quiz_wrong_answer(mock_get_hw, mock_save_sub):
    mock_get_hw.return_value = {"code": "MATH42", "quiz_questions": SAMPLE_QUIZ}
    mock_save_sub.return_value = True
    response = client.post(
        "/h/MATH42/submit",
        json={
            "student_name": "Chidi",
            "student_class": "SS2",
            "answers": [0],
        },
    )
    assert response.status_code == 200
    assert response.json()["score"] == 0


# --- Web Teacher Profile API Tests ---


@patch("classgen.api.teacher.get_teacher_by_phone")
def test_teacher_profile_unregistered(mock_get):
    mock_get.return_value = None
    response = client.get("/api/teacher/profile?thread_id=chat_test123")
    assert response.status_code == 200
    assert response.json()["registered"] is False


@patch("classgen.api.teacher.list_homework_codes_for_teacher", return_value=[])
@patch(
    "classgen.api.teacher.get_teacher_lesson_stats",
    return_value={"total": 5, "this_week": 2, "this_month": 3},
)
@patch("classgen.api.teacher.get_teacher_by_phone")
def test_teacher_profile_registered(mock_get, mock_stats, mock_codes):
    mock_get.return_value = {"name": "Mrs. Test", "slug": "mrs-test", "classes": ["SS2 Biology"]}
    response = client.get("/api/teacher/profile?thread_id=chat_test123")
    assert response.status_code == 200
    data = response.json()
    assert data["registered"] is True
    assert data["teacher"]["name"] == "Mrs. Test"
    assert data["stats"]["total"] == 5


@patch("classgen.api.teacher.save_teacher")
def test_teacher_register(mock_save):
    mock_save.return_value = {"name": "Mrs. Okafor", "slug": "mrs-okafor", "classes": []}
    response = client.post(
        "/api/teacher/register", json={"thread_id": "chat_abc123", "name": "Mrs. Okafor"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["registered"] is True
    assert data["teacher"]["name"] == "Mrs. Okafor"


@patch("classgen.api.teacher.save_teacher")
def test_teacher_register_with_country(mock_save):
    mock_save.return_value = {
        "name": "Mrs. Okafor",
        "slug": "mrs-okafor",
        "classes": [],
        "country": "Nigeria",
    }
    response = client.post(
        "/api/teacher/register",
        json={"thread_id": "chat_abc123", "name": "Mrs. Okafor", "country": "Nigeria"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher"]["country"] == "Nigeria"
    # save_teacher must receive the country, not silently drop it.
    mock_save.assert_called_once_with("chat_abc123", "Mrs. Okafor", country="Nigeria")


def test_teacher_register_short_name():
    response = client.post("/api/teacher/register", json={"thread_id": "chat_abc123", "name": "X"})
    assert response.status_code == 422


@patch("classgen.api.teacher.update_teacher_name")
def test_teacher_update_name(mock_update):
    mock_update.return_value = {"name": "Mrs. New Name", "slug": "mrs-new-name", "classes": []}
    response = client.patch(
        "/api/teacher/profile", json={"thread_id": "chat_abc123", "name": "Mrs. New Name"}
    )
    assert response.status_code == 200
    assert response.json()["teacher"]["name"] == "Mrs. New Name"


@patch("classgen.api.teacher.get_teacher_by_phone")
@patch("classgen.api.teacher.add_teacher_class")
def test_teacher_add_class(mock_add, mock_get):
    mock_get.side_effect = [
        {"name": "T", "slug": "t", "classes": []},
        {"name": "T", "slug": "t", "classes": ["SS2 Biology"]},
    ]
    mock_add.return_value = True
    response = client.post(
        "/api/teacher/classes", json={"thread_id": "chat_abc123", "class_name": "SS2 Biology"}
    )
    assert response.status_code == 200
    assert "SS2 Biology" in response.json()["classes"]


@patch("classgen.api.teacher.get_teacher_by_phone")
@patch("classgen.api.teacher.remove_teacher_class")
def test_teacher_remove_class(mock_remove, mock_get):
    mock_get.side_effect = [
        {"name": "T", "slug": "t", "classes": ["SS2 Biology"]},
        {"name": "T", "slug": "t", "classes": []},
    ]
    mock_remove.return_value = True
    response = client.delete("/api/teacher/classes/SS2%20Biology?thread_id=chat_abc123")
    assert response.status_code == 200
    assert response.json()["classes"] == []


@patch("classgen.api.teacher.clear_session_history")
def test_clear_history(mock_clear):
    mock_clear.return_value = True
    response = client.delete("/api/teacher/history?thread_id=chat_abc123")
    assert response.status_code == 200
    assert response.json()["ok"] is True


# --- Web Chat API Test ---


@patch("classgen.api.chat.get_teacher_by_phone")
@patch("classgen.api.chat.check_usage")
@patch("classgen.api.chat.log_usage")
@patch("classgen.api.chat.handle_command", return_value=None)
@patch("classgen.api.chat.generate_pdf_from_markdown")
@patch("classgen.api.chat.get_session_history")
@patch("classgen.api.chat.log_session")
@patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
@patch("classgen.api.chat.generate_homework_code", return_value="WEB001")
@patch("classgen.api.chat.save_homework_code")
def test_chat_with_registered_teacher(
    mock_save_code,
    mock_gen_code,
    mock_llm,
    mock_log,
    mock_history,
    mock_pdf,
    mock_cmd,
    mock_log_usage,
    mock_check,
    mock_get_teacher,
):
    mock_get_teacher.return_value = {"name": "Mrs. Web", "slug": "mrs-web", "classes": []}
    mock_check.return_value = type(
        "U", (), {"allowed": True, "remaining": 4, "tier": "free", "message": ""}
    )()
    mock_history.return_value = []
    mock_llm.side_effect = [SAMPLE_LESSON_RESPONSE, "[]"]
    mock_pdf.return_value = "lesson_plan_web.pdf"

    response = client.post(
        "/api/chat",
        json={"message": "SS3 Chemistry: Organic Reactions", "thread_id": "chat_registered"},
    )
    assert response.status_code == 200
    mock_check.assert_called_once_with("chat_registered")
    mock_save_code.assert_called_once()


# --- Clarification rendering ---


@patch("classgen.api.chat.save_homework_code")
@patch("classgen.api.chat.generate_pdf_from_markdown")
@patch("classgen.api.chat.log_session")
@patch("classgen.api.chat.get_session_history", return_value=[])
@patch("classgen.api.chat.call_openrouter_json", new_callable=AsyncMock)
def test_chat_clarification_rendered_as_suggestions(
    mock_llm,
    mock_hist,
    mock_log,
    mock_pdf,
    mock_save,
):
    """When the LLM responds with the V4.1 clarification JSON shape, the
    blocking endpoint must rewrite ``reply`` into the SUGGESTIONS: format
    the web frontend already renders as quick-reply buttons. Otherwise the
    user sees raw JSON in the chat (the production bug we're fixing)."""
    mock_llm.return_value = (
        '{"clarification": "What class level is this for?",'
        ' "suggestions": ["JSS1", "JSS2", "SS1"]}'
    )
    with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True):
        response = client.post(
            "/api/chat",
            json={"message": "Linear equations", "thread_id": "clarif-thread"},
        )
    assert response.status_code == 200
    data = response.json()

    # No raw JSON braces leaking into the reply
    assert "{" not in data["reply"]
    assert '"clarification"' not in data["reply"]

    # Question is preserved + SUGGESTIONS line is present in the format
    # the existing frontend regex (index.html:1136) understands
    assert data["reply"].startswith("What class level is this for?")
    assert "SUGGESTIONS:" in data["reply"]
    assert "[JSS1]" in data["reply"]
    assert "[JSS2]" in data["reply"]
    assert "[SS1]" in data["reply"]

    # No PDF / homework should be generated for a clarification turn
    assert data["pdf_url"] is None
    assert data["homework_code"] is None
    assert "lesson_pack" not in data
    mock_save.assert_not_called()
    mock_pdf.assert_not_called()


@patch("classgen.api.chat.save_homework_code")
@patch("classgen.api.chat.generate_pdf_from_markdown")
@patch("classgen.api.chat.log_session")
@patch("classgen.api.chat.get_session_history", return_value=[])
@patch("classgen.api.chat.call_openrouter_json", new_callable=AsyncMock)
def test_chat_clarification_without_suggestions(
    mock_llm,
    mock_hist,
    mock_log,
    mock_pdf,
    mock_save,
):
    """A clarification with an empty/missing suggestions array should still
    render as a clean question — no trailing 'SUGGESTIONS:' line dangling."""
    mock_llm.return_value = '{"clarification": "Tell me more."}'
    with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True):
        response = client.post(
            "/api/chat",
            json={"message": "?", "thread_id": "clarif-empty"},
        )
    data = response.json()
    assert data["reply"] == "Tell me more."
    assert "SUGGESTIONS:" not in data["reply"]
