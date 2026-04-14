"""Tests for WhatsApp flow session engine and lesson browse flow."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from classgen.api.app import app
from classgen.commands.handlers import _handle_lesson_flow
from classgen.commands.router import CommandResult
from classgen.core.models import (
    ActivityBlock,
    ExplainBlock,
    HomeworkBlock,
    HomeworkTask,
    KeyTerm,
    LessonMeta,
    LessonPack,
    OpenerBlock,
    TeacherNotesBlock,
)
from classgen.data.wa_flows import WAFlow, clear_flow, get_flow, set_flow, update_flow

client = TestClient(app)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PACK = LessonPack(
    meta=LessonMeta(subject="Biology", topic="Photosynthesis", class_level="SS2"),
    blocks=[
        OpenerBlock(
            title="Kitchen Water Cycle",
            body="Boil water and watch the cycle.",
            format="what_if",
            duration_minutes=2,
            props=["Kettle", "Cold plate"],
        ),
        ExplainBlock(
            title="Evaporation and Condensation",
            body="Two key processes in the water cycle.",
            wow_fact="Earth has had the same water for 3B years.",
            analogy="Like a crowd leaving a stadium.",
            key_terms=[KeyTerm(term="Evaporation", definition="liquid to gas")],
        ),
        ActivityBlock(
            title="Water Cycle Relay",
            body="Students race to label stages.",
            format="relay_race",
            group_size=5,
            duration_minutes=12,
            materials=["Chart paper", "markers"],
            rules=["Label one stage", "Pass the chart"],
            expected_outcome="Students can sequence all 4 stages.",
        ),
        HomeworkBlock(
            title="Water Detective",
            body="Observe the water cycle at home.",
            format="investigation",
            tasks=[
                HomeworkTask(id="t1", instruction="Find 3 examples of evaporation"),
                HomeworkTask(id="t2", instruction="Record temperature"),
            ],
            completion="Share findings Monday.",
        ),
        TeacherNotesBlock(
            title="Common Misconceptions",
            body="Students often confuse evaporation with boiling.",
            common_mistakes=["Confusing evaporation with boiling"],
            quick_assessment="Ask where puddle water goes.",
            exam_tip="WAEC frequently tests water cycle.",
        ),
    ],
)

PHONE = "whatsapp:+2348012345678"


def _make_flow() -> WAFlow:
    return WAFlow(
        type="lesson_browse",
        step="menu",
        data={
            "lesson_pack": SAMPLE_PACK.model_dump(),
            "homework_code": "BIO42",
            "pdf_url": "http://localhost:8000/static/lesson.pdf",
            "current_block": 0,
        },
    )


# ---------------------------------------------------------------------------
# Flow storage tests
# ---------------------------------------------------------------------------


class TestFlowStorage:
    def setup_method(self):
        clear_flow(PHONE)

    def test_set_and_get(self):
        flow = _make_flow()
        set_flow(PHONE, flow)
        retrieved = get_flow(PHONE)
        assert retrieved is not None
        assert retrieved.type == "lesson_browse"
        assert retrieved.data["homework_code"] == "BIO42"

    def test_get_nonexistent_returns_none(self):
        assert get_flow("whatsapp:+0000000000") is None

    def test_update_step(self):
        set_flow(PHONE, _make_flow())
        update_flow(PHONE, step="viewing")
        flow = get_flow(PHONE)
        assert flow is not None
        assert flow.step == "viewing"

    def test_update_data_merges(self):
        set_flow(PHONE, _make_flow())
        update_flow(PHONE, data={"current_block": 3})
        flow = get_flow(PHONE)
        assert flow is not None
        assert flow.data["current_block"] == 3
        assert flow.data["homework_code"] == "BIO42"  # not overwritten

    def test_clear(self):
        set_flow(PHONE, _make_flow())
        clear_flow(PHONE)
        assert get_flow(PHONE) is None

    def test_replace_flow(self):
        set_flow(PHONE, _make_flow())
        new_flow = WAFlow(type="register", step="name", data={"partial": True})
        set_flow(PHONE, new_flow)
        retrieved = get_flow(PHONE)
        assert retrieved is not None
        assert retrieved.type == "register"


# ---------------------------------------------------------------------------
# Lesson browse flow handler tests
# ---------------------------------------------------------------------------


class TestLessonBrowseFlow:
    def setup_method(self):
        clear_flow(PHONE)
        set_flow(PHONE, _make_flow())

    def test_sections_command(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "sections", PHONE)
        assert isinstance(result, CommandResult)
        assert "Photosynthesis" in result.reply
        assert "Hook" in result.reply
        assert "Concept" in result.reply

    def test_block_by_number(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "1", PHONE)
        assert isinstance(result, CommandResult)
        assert "Hook" in result.reply
        assert "Kitchen Water Cycle" in result.reply

    def test_block_by_number_out_of_range(self):
        flow = get_flow(PHONE)
        # Pack has 5 blocks, so "5" is valid
        result = _handle_lesson_flow(flow, "5", PHONE)
        assert isinstance(result, CommandResult)
        assert "Notes" in result.reply or "Teacher Notes" in result.reply

    def test_block_by_name(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "homework", PHONE)
        assert isinstance(result, CommandResult)
        assert "Homework" in result.reply
        assert "Water Detective" in result.reply

    def test_next_from_start(self):
        flow = get_flow(PHONE)
        # current_block starts at 0, next should go to 1
        result = _handle_lesson_flow(flow, "next", PHONE)
        assert isinstance(result, CommandResult)
        # After next from block 0, should show block 1 (Explain)
        assert "Concept" in result.reply or "Evaporation" in result.reply

    def test_prev_from_start(self):
        flow = get_flow(PHONE)
        # prev from 0 stays at 0
        result = _handle_lesson_flow(flow, "prev", PHONE)
        assert isinstance(result, CommandResult)
        assert "Hook" in result.reply

    def test_full_lesson(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "full", PHONE)
        assert isinstance(result, CommandResult)
        assert "Hook" in result.reply
        assert "Concept" in result.reply
        assert "Activity" in result.reply
        assert "Homework" in result.reply

    def test_pdf_link(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "pdf", PHONE)
        assert isinstance(result, CommandResult)
        assert "lesson.pdf" in result.reply

    def test_done_clears_flow(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "done", PHONE)
        assert isinstance(result, CommandResult)
        assert "closed" in result.reply.lower()
        assert get_flow(PHONE) is None

    def test_unknown_input_falls_through(self):
        flow = get_flow(PHONE)
        result = _handle_lesson_flow(flow, "SS2 Chemistry: Atomic Structure", PHONE)
        assert result is None  # falls through to LLM


class TestFlowFallthrough:
    """Navigation keywords without an active flow should not be intercepted."""

    def setup_method(self):
        clear_flow(PHONE)

    @patch("classgen.api.webhook.call_openrouter", return_value="Not a command response")
    def test_sections_without_flow_goes_to_llm(self, mock_llm):
        """'sections' with no active flow should not be intercepted by flow dispatch."""
        from classgen.commands.router import handle_command

        result = handle_command("sections", PHONE, "http://localhost:8000")
        # No flow active, so this should fall through (return None)
        assert result is None

    def test_number_without_flow_goes_to_llm(self):
        from classgen.commands.router import handle_command

        result = handle_command("1", PHONE, "http://localhost:8000")
        assert result is None

    def test_homework_without_flow_goes_to_llm(self):
        from classgen.commands.router import handle_command

        result = handle_command("homework", PHONE, "http://localhost:8000")
        assert result is None


class TestFlowDispatchInRouter:
    """Flow dispatch integrates correctly with the command router."""

    def setup_method(self):
        clear_flow(PHONE)

    def test_sections_with_active_flow(self):
        set_flow(PHONE, _make_flow())
        from classgen.commands.router import handle_command

        result = handle_command("sections", PHONE, "http://localhost:8000")
        assert result is not None
        assert "Photosynthesis" in result.reply

    def test_existing_commands_still_work_with_flow(self):
        """Commands like 'help' should still work even with an active flow."""
        set_flow(PHONE, _make_flow())
        from classgen.commands.router import handle_command

        result = handle_command("help", PHONE, "http://localhost:8000")
        assert result is not None
        assert "Commands" in result.reply
