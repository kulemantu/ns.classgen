"""Integration tests tracing core user journeys through the V4 module structure.

Each test exercises the full request→router→service→data path with minimal
mocking (only the LLM and external services are mocked, not internal modules).
These verify that the restructured imports actually connect correctly at runtime.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from classgen.api.app import app

client = TestClient(app)

LESSON_WITH_BLOCKS = """[BLOCK_START_OPENER]
Title: The Amazing Water Cycle
Summary: Water never disappears — it just moves.
Details: Hold a cold plate over boiling water. Watch the droplets form.
[BLOCK_END]

[BLOCK_START_EXPLAIN]
Title: How Water Moves Around Earth
Summary: Evaporation, condensation, precipitation.
Details: The sun heats water, it evaporates, forms clouds, and falls as rain.
[BLOCK_END]

[BLOCK_START_ACTIVITY]
Title: Water Cycle Relay Race
Summary: Teams race to sequence the water cycle steps.
Details: Groups of 5. Each person writes one step on the board.
[BLOCK_END]

[BLOCK_START_HOMEWORK]
Title: Water Detective Challenge
Summary: Story problem
Details: You are a water engineer investigating why a village well is drying up.
Task 1: Draw the water cycle and label all 4 stages.
Task 2: Calculate how many litres of rain fall on a 10m x 10m roof in 5mm of rainfall.
Task 3: Write a one-paragraph report to the village chief explaining your findings.
[BLOCK_END]

[BLOCK_START_TEACHER_NOTES]
Title: Teacher Reference
Summary: Quick reference for the teacher.
Details: Expected answers: 500 litres (10 x 10 x 0.005 x 1000).
Common mistake: students forget to convert mm to metres.
[BLOCK_END]"""

QUIZ_JSON = '[{"question":"What drives the water cycle?","options":["Wind","Sun","Moon","Gravity"],"correct":1}]'


# ---------------------------------------------------------------------------
# Journey 1: Teacher generates a lesson via web chat
# ---------------------------------------------------------------------------


class TestWebChatLessonGeneration:
    """Teacher opens web UI, sends a topic, receives a structured lesson."""

    @patch("classgen.api.chat.generate_pdf_from_markdown", return_value="lesson_abc.pdf")
    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    def test_full_lesson_flow(self, mock_llm, mock_pdf):
        """Given a topic, the chat endpoint returns a lesson with blocks, PDF, and homework code."""
        mock_llm.side_effect = [LESSON_WITH_BLOCKS, QUIZ_JSON]

        response = client.post(
            "/api/chat",
            json={
                "message": "SS2 Geography: Water Cycle, 40 minutes",
                "thread_id": "test_web_001",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Water Cycle" in data["reply"]
        assert "[BLOCK_START_OPENER]" in data["reply"]
        assert data["pdf_url"] is not None
        assert data["homework_code"] is not None
        assert len(data["homework_code"]) == 6

    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    def test_clarifying_question_no_homework(self, mock_llm):
        """When the LLM asks a clarifying question (no blocks), no PDF or homework is generated."""
        mock_llm.return_value = (
            "What grade level? SS1, SS2, or SS3?\nSUGGESTIONS: [SS1] | [SS2] | [SS3]"
        )

        response = client.post(
            "/api/chat",
            json={
                "message": "biology",
                "thread_id": "test_web_002",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "grade level" in data["reply"].lower()
        assert data["pdf_url"] is None
        assert data["homework_code"] is None

    @patch("classgen.api.chat.call_openrouter", new_callable=AsyncMock)
    def test_llm_failure_graceful(self, mock_llm):
        """When the LLM returns None (API error), the user gets a friendly message."""
        mock_llm.return_value = None

        response = client.post(
            "/api/chat",
            json={
                "message": "SS1 Maths: Algebra",
                "thread_id": "test_web_003",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "resting" in data["reply"].lower()


# ---------------------------------------------------------------------------
# Journey 2: Student takes a homework quiz
# ---------------------------------------------------------------------------


class TestStudentQuizFlow:
    """Student receives a homework code, visits the page, takes the quiz."""

    def test_homework_page_serves_html(self):
        """The homework page serves homework.html for valid codes (after seeding)."""
        # Seed a homework code via the data layer directly
        from classgen.data.homework import save_homework_code

        save_homework_code(
            code="INTG01",
            thread_id="test_teacher",
            lesson_content=LESSON_WITH_BLOCKS,
            quiz_questions=[
                {
                    "question": "What drives the water cycle?",
                    "options": ["Wind", "Sun", "Moon", "Gravity"],
                    "correct": 1,
                },
                {
                    "question": "What is evaporation?",
                    "options": ["Rain", "Water to gas", "Ice melting", "Flooding"],
                    "correct": 1,
                },
            ],
            homework_block="Title: Water Detective\nDetails: Investigate the water cycle.",
        )

        # Student visits the homework page
        response = client.get("/h/INTG01")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_homework_api_returns_data(self):
        """The homework data API returns structured quiz data."""
        response = client.get("/api/h/INTG01")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "INTG01"
        assert len(data["quiz_questions"]) == 2
        assert data["homework_block"].startswith("Title: Water Detective")

    def test_quiz_submission_grading(self):
        """Student submits answers and gets correct grading."""
        response = client.post(
            "/h/INTG01/submit",
            json={
                "student_name": "Amina",
                "student_class": "SS2",
                "answers": [1, 1],  # both correct
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 2
        assert data["total"] == 2
        assert all(r["is_correct"] for r in data["results"])

    def test_quiz_submission_partial(self):
        """Student gets partial score with some wrong answers."""
        response = client.post(
            "/h/INTG01/submit",
            json={
                "student_name": "Chidi",
                "student_class": "SS2",
                "answers": [0, 1],  # first wrong, second correct
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1
        assert data["total"] == 2

    def test_results_api(self):
        """Teacher can see quiz results for a homework code."""
        response = client.get("/api/h/INTG01/results")
        assert response.status_code == 200
        data = response.json()
        assert data["total_submissions"] == 2
        assert data["average_score"] > 0


# ---------------------------------------------------------------------------
# Journey 3: Teacher registers and manages profile
# ---------------------------------------------------------------------------


class TestTeacherProfileFlow:
    """Teacher registers, adds classes, views profile."""

    def test_register_teacher(self):
        """Teacher registers with a name and gets a profile."""
        response = client.post(
            "/api/teacher/register",
            json={
                "thread_id": "teacher_intg_001",
                "name": "Mrs. Integration",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["registered"] is True
        assert data["teacher"]["name"] == "Mrs. Integration"
        assert "slug" in data["teacher"]

    def test_profile_after_registration(self):
        """After registration, the teacher profile API returns their data."""
        response = client.get("/api/teacher/profile?thread_id=teacher_intg_001")
        assert response.status_code == 200
        data = response.json()
        assert data["registered"] is True
        assert data["teacher"]["name"] == "Mrs. Integration"

    def test_add_class(self):
        """Teacher can add a class to their profile."""
        response = client.post(
            "/api/teacher/classes",
            json={
                "thread_id": "teacher_intg_001",
                "class_name": "SS2 Biology",
            },
        )
        assert response.status_code == 200
        assert "SS2 Biology" in response.json()["classes"]

    def test_remove_class(self):
        """Teacher can remove a class from their profile."""
        response = client.delete("/api/teacher/classes/SS2%20Biology?thread_id=teacher_intg_001")
        assert response.status_code == 200
        assert "SS2 Biology" not in response.json()["classes"]


# ---------------------------------------------------------------------------
# Journey 4: Command routing
# ---------------------------------------------------------------------------


class TestCommandRouting:
    """WhatsApp commands route correctly through the new module structure."""

    def test_help_command(self):
        """The help command returns command list without hitting LLM."""
        from classgen.commands.router import handle_command

        result = handle_command("help", "+2341234567890", "https://class.dater.world")
        assert result is not None
        assert "Commands" in result.reply

    def test_greeting_handled(self):
        """Greetings are handled without LLM."""
        from classgen.commands.router import handle_command

        result = handle_command("hello", "+2341234567890", "https://class.dater.world")
        assert result is not None
        assert "Welcome" in result.reply

    def test_unknown_text_falls_through(self):
        """Non-command text returns None (falls through to LLM)."""
        from classgen.commands.router import handle_command

        result = handle_command(
            "SS2 Biology: Photosynthesis", "+2341234567890", "https://class.dater.world"
        )
        assert result is None

    def test_register_flow(self):
        """Register command creates a teacher profile."""
        from classgen.commands.router import handle_command

        result = handle_command(
            "register Mrs. CommandTest", "+23400001111", "https://class.dater.world"
        )
        assert result is not None
        assert "Mrs. CommandTest" in result.reply
        assert "/t/" in result.reply


# ---------------------------------------------------------------------------
# Journey 5: Data layer (in-memory fallback)
# ---------------------------------------------------------------------------


class TestDataLayerInMemory:
    """Data layer works correctly with in-memory fallback (no Supabase)."""

    def test_session_log_and_retrieve(self):
        from classgen.data.sessions import get_session_history, log_session

        log_session("intg_thread", "user", "Test message")
        log_session("intg_thread", "assistant", "Test reply")
        history = get_session_history("intg_thread", limit=10)
        assert len(history) >= 2
        assert history[-1]["content"] == "Test reply"

    def test_teacher_save_and_retrieve(self):
        from classgen.data.teachers import get_teacher_by_phone, get_teacher_by_slug, save_teacher

        teacher = save_teacher("+23499990000", "Dr. DataTest")
        assert teacher["name"] == "Dr. DataTest"
        assert teacher["slug"].startswith("dr-")

        by_phone = get_teacher_by_phone("+23499990000")
        assert by_phone is not None
        assert by_phone["name"] == "Dr. DataTest"

        by_slug = get_teacher_by_slug(teacher["slug"])
        assert by_slug is not None

    def test_lesson_cache(self):
        from classgen.data.lessons import cache_lesson, get_cached_lesson

        cache_lesson("Biology", "Photosynthesis", "SS2", "cached content here")
        cached = get_cached_lesson("Biology", "Photosynthesis", "SS2")
        assert cached == "cached content here"

    def test_curriculum_suggest(self):
        from classgen.content.curriculum import suggest_topics

        uncovered, covered = suggest_topics("WAEC", "Biology", "SS1", [])
        assert len(uncovered) > 0
        assert len(covered) == 0
