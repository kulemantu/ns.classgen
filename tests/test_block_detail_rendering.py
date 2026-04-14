"""Tests for WhatsApp block detail rendering."""

from __future__ import annotations

from classgen.channels.whatsapp import WhatsAppAdapter
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

adapter = WhatsAppAdapter()


# ---------------------------------------------------------------------------
# Sample blocks
# ---------------------------------------------------------------------------

OPENER = OpenerBlock(
    title="Kitchen Water Cycle",
    body="Boil water and watch the cycle. Steam rises, condenses on cold plate.",
    format="what_if",
    duration_minutes=2,
    props=["Kettle", "Cold plate", "Thermometer"],
)

EXPLAIN = ExplainBlock(
    title="Evaporation and Condensation",
    body="Two key processes in the water cycle.",
    wow_fact="Earth has had the same water for 3 billion years.",
    analogy="Like a crowd leaving a stadium — one by one.",
    key_terms=[
        KeyTerm(term="Evaporation", definition="liquid to gas"),
        KeyTerm(term="Condensation", definition="gas to liquid"),
    ],
    equation="H2O(l) -> H2O(g)",
)

ACTIVITY = ActivityBlock(
    title="Water Cycle Relay",
    body="Students race to label water cycle stages.",
    format="relay_race",
    group_size=5,
    duration_minutes=12,
    materials=["Chart paper", "markers", "timer"],
    rules=["Label one stage each", "Pass chart to next person"],
    expected_outcome="Students can sequence all 4 stages.",
)

HOMEWORK = HomeworkBlock(
    title="Water Detective",
    body="Observe the water cycle at home this weekend.",
    format="investigation",
    tasks=[
        HomeworkTask(id="t1", instruction="Find 3 examples of evaporation"),
        HomeworkTask(id="t2", instruction="Record temperature near each source"),
        HomeworkTask(id="t3", instruction="Draw what you observe"),
    ],
    completion="Share findings in class Monday.",
)

NOTES = TeacherNotesBlock(
    title="Common Misconceptions",
    body="Students often confuse evaporation with boiling.",
    common_mistakes=[
        "Confusing evaporation with boiling",
        "Forgetting condensation requires cooling",
    ],
    quick_assessment='Ask "Where does the water go when a puddle dries?"',
    exam_tip="WAEC frequently tests the water cycle diagram.",
)

ALL_BLOCKS = [OPENER, EXPLAIN, ACTIVITY, HOMEWORK, NOTES]

PACK = LessonPack(
    meta=LessonMeta(subject="Biology", topic="Photosynthesis", class_level="SS2"),
    blocks=ALL_BLOCKS,
)


# ---------------------------------------------------------------------------
# Block detail rendering
# ---------------------------------------------------------------------------


class TestOpenerDetail:
    def test_renders_title_and_label(self):
        text = adapter.render_block_detail(OPENER, 0, 5, blocks=ALL_BLOCKS)
        assert "Hook" in text
        assert "Kitchen Water Cycle" in text

    def test_renders_format_and_duration(self):
        text = adapter.render_block_detail(OPENER, 0, 5, blocks=ALL_BLOCKS)
        assert "2 min" in text
        assert "what_if" in text

    def test_renders_props(self):
        text = adapter.render_block_detail(OPENER, 0, 5, blocks=ALL_BLOCKS)
        assert "Kettle" in text
        assert "Thermometer" in text

    def test_renders_nav_footer(self):
        text = adapter.render_block_detail(OPENER, 0, 5, blocks=ALL_BLOCKS)
        assert "next" in text
        assert "Concept" in text  # next block label


class TestExplainDetail:
    def test_renders_key_terms(self):
        text = adapter.render_block_detail(EXPLAIN, 1, 5, blocks=ALL_BLOCKS)
        assert "Evaporation" in text
        assert "liquid to gas" in text

    def test_renders_wow_fact(self):
        text = adapter.render_block_detail(EXPLAIN, 1, 5, blocks=ALL_BLOCKS)
        assert "3 billion years" in text

    def test_renders_analogy(self):
        text = adapter.render_block_detail(EXPLAIN, 1, 5, blocks=ALL_BLOCKS)
        assert "crowd leaving" in text

    def test_renders_equation(self):
        text = adapter.render_block_detail(EXPLAIN, 1, 5, blocks=ALL_BLOCKS)
        assert "H2O" in text


class TestActivityDetail:
    def test_renders_materials(self):
        text = adapter.render_block_detail(ACTIVITY, 2, 5, blocks=ALL_BLOCKS)
        assert "Chart paper" in text
        assert "timer" in text

    def test_renders_rules(self):
        text = adapter.render_block_detail(ACTIVITY, 2, 5, blocks=ALL_BLOCKS)
        assert "Label one stage" in text

    def test_renders_group_info(self):
        text = adapter.render_block_detail(ACTIVITY, 2, 5, blocks=ALL_BLOCKS)
        assert "Groups of 5" in text
        assert "12 min" in text


class TestHomeworkDetail:
    def test_renders_tasks(self):
        text = adapter.render_block_detail(HOMEWORK, 3, 5, blocks=ALL_BLOCKS)
        assert "Find 3 examples" in text
        assert "Record temperature" in text

    def test_renders_completion(self):
        text = adapter.render_block_detail(HOMEWORK, 3, 5, blocks=ALL_BLOCKS)
        assert "Monday" in text


class TestTeacherNotesDetail:
    def test_renders_mistakes(self):
        text = adapter.render_block_detail(NOTES, 4, 5, blocks=ALL_BLOCKS)
        assert "evaporation with boiling" in text

    def test_renders_assessment(self):
        text = adapter.render_block_detail(NOTES, 4, 5, blocks=ALL_BLOCKS)
        assert "puddle" in text

    def test_renders_exam_tip(self):
        text = adapter.render_block_detail(NOTES, 4, 5, blocks=ALL_BLOCKS)
        assert "WAEC" in text

    def test_last_block_no_next(self):
        text = adapter.render_block_detail(NOTES, 4, 5, blocks=ALL_BLOCKS)
        # Last block should not say "next for X"
        assert "Reply 'next' for" not in text
        assert "new topic" in text


# ---------------------------------------------------------------------------
# Sections menu
# ---------------------------------------------------------------------------


class TestSectionsMenu:
    def test_shows_topic(self):
        text = adapter.render_sections_menu(PACK)
        assert "Photosynthesis" in text

    def test_shows_all_blocks(self):
        text = adapter.render_sections_menu(PACK)
        assert "Hook" in text
        assert "Concept" in text
        assert "Activity" in text
        assert "Homework" in text
        assert "Notes" in text

    def test_shows_numbers(self):
        text = adapter.render_sections_menu(PACK)
        # Number emojis or numbers should be present
        for block in PACK.blocks:
            label = {
                "opener": "Hook",
                "explain": "Concept",
                "activity": "Activity",
                "homework": "Homework",
                "teacher_notes": "Notes",
            }
            assert label.get(block.type, block.type) in text

    def test_shows_nav_hint(self):
        text = adapter.render_sections_menu(PACK)
        assert "1-5" in text or "number" in text
        assert "pdf" in text


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------


class TestTruncation:
    def test_long_body_truncated(self):
        long_block = OpenerBlock(
            title="Long Test",
            body="x" * 1000,
            format="what_if",
        )
        text = adapter.render_block_detail(long_block, 0, 1)
        assert len(text) < 1500
        assert "..." in text
