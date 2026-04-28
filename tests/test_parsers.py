"""Tests for classgen.core.parsers — dual JSON + block-marker parsing."""

from classgen.core.models import (
    ActivityBlock,
    ExplainBlock,
    HomeworkBlock,
    LessonPack,
    OpenerBlock,
    TeacherNotesBlock,
)
from classgen.core.parsers import (
    parse_clarification,
    parse_lesson_blocks,
    parse_lesson_json,
    parse_lesson_response,
)
from tests.fixtures import (
    BROKEN_LESSON_NO_MARKERS,
    SAMPLE_LESSON_BLOCKS,
    SAMPLE_LESSON_JSON,
    SAMPLE_LESSON_OLD_NAMES,
)


class TestParseLessonJSON:
    def test_valid_json(self):
        pack = parse_lesson_json(SAMPLE_LESSON_JSON)
        assert pack is not None
        assert isinstance(pack, LessonPack)
        assert len(pack.blocks) == 5
        assert pack.meta.subject == "Biology"

    def test_json_with_code_fences(self):
        fenced = f"```json\n{SAMPLE_LESSON_JSON}\n```"
        pack = parse_lesson_json(fenced)
        assert pack is not None
        assert len(pack.blocks) == 5

    def test_json_with_bare_fences(self):
        fenced = f"```\n{SAMPLE_LESSON_JSON}\n```"
        pack = parse_lesson_json(fenced)
        assert pack is not None

    def test_malformed_json(self):
        assert parse_lesson_json("{bad json") is None

    def test_empty_string(self):
        assert parse_lesson_json("") is None

    def test_json_array_not_object(self):
        assert parse_lesson_json("[1, 2, 3]") is None

    def test_json_missing_blocks(self):
        pack = parse_lesson_json('{"version": "4.0", "meta": {}}')
        # Valid JSON, valid LessonPack, but no blocks
        assert pack is not None
        assert pack.blocks == []

    def test_json_invalid_block_type(self):
        bad = '{"blocks": [{"type": "bogus", "title": "x", "body": "y"}]}'
        assert parse_lesson_json(bad) is None


class TestParseLessonBlocks:
    def test_standard_blocks(self):
        pack = parse_lesson_blocks(SAMPLE_LESSON_BLOCKS)
        assert pack is not None
        assert len(pack.blocks) == 5
        assert isinstance(pack.blocks[0], OpenerBlock)
        assert isinstance(pack.blocks[1], ExplainBlock)
        assert isinstance(pack.blocks[2], ActivityBlock)
        assert isinstance(pack.blocks[3], HomeworkBlock)
        assert isinstance(pack.blocks[4], TeacherNotesBlock)

    def test_block_titles_extracted(self):
        pack = parse_lesson_blocks(SAMPLE_LESSON_BLOCKS)
        assert pack is not None
        assert pack.blocks[0].title == "What if photosynthesis stopped tomorrow?"
        assert pack.blocks[1].title == "The Factory Inside Every Leaf"

    def test_block_body_contains_details(self):
        pack = parse_lesson_blocks(SAMPLE_LESSON_BLOCKS)
        assert pack is not None
        assert "solar-powered factory" in pack.blocks[1].body

    def test_old_block_names_mapped(self):
        """HOOK → opener, FACT → explain (backward compat with test_main.py fixtures)."""
        pack = parse_lesson_blocks(SAMPLE_LESSON_OLD_NAMES)
        assert pack is not None
        assert len(pack.blocks) == 3
        assert isinstance(pack.blocks[0], OpenerBlock)
        assert pack.blocks[0].title == "The Water Cycle in Your Kitchen"
        assert isinstance(pack.blocks[1], ExplainBlock)
        assert pack.blocks[1].title == "Earth Has the Same Water as the Dinosaurs"
        assert isinstance(pack.blocks[2], HomeworkBlock)

    def test_no_blocks_returns_none(self):
        assert parse_lesson_blocks("Just a clarifying question") is None

    def test_empty_string(self):
        assert parse_lesson_blocks("") is None

    def test_partial_block_markers_ignored(self):
        # Only opening marker, no closing
        assert parse_lesson_blocks("[BLOCK_START_OPENER] some text") is None

    def test_application_legacy_name_mapped(self):
        """APPLICATION → activity (legacy block name mapping)."""
        text = (
            "[BLOCK_START_APPLICATION]\n"
            "Title: Team Challenge\n"
            "Summary: Group work\n"
            "Details: Split into teams.\n"
            "[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert len(pack.blocks) == 1
        assert isinstance(pack.blocks[0], ActivityBlock)
        assert pack.blocks[0].title == "Team Challenge"

    def test_unknown_block_type_skipped(self):
        """Block with unrecognized type is silently skipped."""
        text = (
            "[BLOCK_START_UNKNOWN]\n"
            "Title: Mystery\nDetails: Content\n"
            "[BLOCK_END]\n"
            "[BLOCK_START_OPENER]\n"
            "Title: Real Block\nDetails: Real content\n"
            "[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert len(pack.blocks) == 1
        assert pack.blocks[0].title == "Real Block"

    def test_block_without_title_structure(self):
        """Block body with no Title/Summary/Details uses fallback."""
        text = (
            "[BLOCK_START_OPENER]\nJust some raw text without the expected structure.\n[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert pack.blocks[0].title == "Opener"
        assert "raw text" in pack.blocks[0].body

    def test_block_title_with_details_no_summary(self):
        """Title and Details present but no Summary line."""
        text = (
            "[BLOCK_START_EXPLAIN]\n"
            "Title: Concept X\n"
            "Details: The full explanation here.\n"
            "[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert pack.blocks[0].title == "Concept X"
        assert "full explanation" in pack.blocks[0].body

    def test_block_title_with_bold_markdown(self):
        """Title wrapped in **bold** markers is stripped."""
        text = (
            "[BLOCK_START_OPENER]\n"
            "Title: **Bold Title**\n"
            "Summary: Test\n"
            "Details: Content\n"
            "[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert pack.blocks[0].title == "Bold Title"

    def test_multiline_details(self):
        """Details spanning multiple lines are captured fully."""
        text = (
            "[BLOCK_START_EXPLAIN]\n"
            "Title: Multi\n"
            "Summary: Brief\n"
            "Details: Line one.\n"
            "Line two continues.\n"
            "Line three ends.\n"
            "[BLOCK_END]"
        )
        pack = parse_lesson_blocks(text)
        assert pack is not None
        assert "Line one" in pack.blocks[0].body
        assert "Line three" in pack.blocks[0].body


class TestParseLessonResponse:
    def test_json_preferred_over_blocks(self):
        pack, raw = parse_lesson_response(SAMPLE_LESSON_JSON)
        assert pack is not None
        assert pack.meta.subject == "Biology"
        assert raw == SAMPLE_LESSON_JSON

    def test_falls_back_to_blocks(self):
        pack, raw = parse_lesson_response(SAMPLE_LESSON_BLOCKS)
        assert pack is not None
        assert len(pack.blocks) == 5
        assert raw == SAMPLE_LESSON_BLOCKS

    def test_neither_format_returns_none(self):
        text = "What class level are we working with?"
        pack, raw = parse_lesson_response(text)
        assert pack is None
        assert raw == text

    def test_raw_text_always_preserved(self):
        _, raw = parse_lesson_response(SAMPLE_LESSON_JSON)
        assert raw == SAMPLE_LESSON_JSON
        _, raw = parse_lesson_response(SAMPLE_LESSON_BLOCKS)
        assert raw == SAMPLE_LESSON_BLOCKS

    def test_empty_blocks_json_falls_back(self):
        """JSON with empty blocks array should try block parser."""
        empty_json = '{"version": "4.0", "blocks": []}'
        pack, _ = parse_lesson_response(empty_json)
        # No blocks in JSON, no blocks in text → None
        assert pack is None


class TestParseClarification:
    """Cover the V4.1 clarification JSON shape produced when the LLM is
    missing context (subject / topic / class level). Each case represents
    a real-world LLM output the parser must classify correctly."""

    def test_well_formed_clarification(self):
        raw = (
            '{"clarification": "What class level is this for?",'
            ' "suggestions": ["JSS1", "JSS2", "SS1"]}'
        )
        result = parse_clarification(raw)
        assert result is not None
        question, suggestions = result
        assert question == "What class level is this for?"
        assert suggestions == ["JSS1", "JSS2", "SS1"]

    def test_clarification_with_code_fence(self):
        """Some models wrap JSON in ```json ... ``` fences. Strip them."""
        raw = (
            "```json\n"
            '{"clarification": "Which subject?", "suggestions": ["Math", "Biology"]}\n'
            "```"
        )
        result = parse_clarification(raw)
        assert result == ("Which subject?", ["Math", "Biology"])

    def test_clarification_without_suggestions(self):
        raw = '{"clarification": "Tell me more about your class."}'
        result = parse_clarification(raw)
        assert result == ("Tell me more about your class.", [])

    def test_clarification_with_null_suggestions(self):
        raw = '{"clarification": "Anything else?", "suggestions": null}'
        result = parse_clarification(raw)
        assert result == ("Anything else?", [])

    def test_clarification_strips_blank_suggestions(self):
        raw = (
            '{"clarification": "Pick one", '
            '"suggestions": ["A", "  ", "", "B", null]}'
        )
        result = parse_clarification(raw)
        assert result is not None
        _, suggestions = result
        # Only non-empty string suggestions survive
        assert suggestions == ["A", "B"]

    def test_lesson_pack_json_is_not_clarification(self):
        """A full LessonPack JSON has no 'clarification' key — must return None."""
        assert parse_clarification(SAMPLE_LESSON_JSON) is None

    def test_block_marker_text_is_not_clarification(self):
        assert parse_clarification(SAMPLE_LESSON_BLOCKS) is None

    def test_plain_text_is_not_clarification(self):
        assert parse_clarification("What class level are we working with?") is None

    def test_malformed_json_returns_none(self):
        assert parse_clarification("{not valid json") is None

    def test_non_dict_json_returns_none(self):
        assert parse_clarification('["clarification", "suggestions"]') is None

    def test_empty_clarification_returns_none(self):
        """A blank or missing clarification field shouldn't be treated as one."""
        assert parse_clarification('{"clarification": "", "suggestions": ["A"]}') is None
        assert parse_clarification('{"clarification": "   "}') is None
        assert parse_clarification('{"suggestions": ["A"]}') is None

    def test_non_string_clarification_returns_none(self):
        assert parse_clarification('{"clarification": 42, "suggestions": []}') is None


class TestNoMarkersRecovery:
    """The LLM occasionally emits Title:/Summary:/Details: triples without the
    surrounding [BLOCK_START_X]/[BLOCK_END] markers. Before the recovery
    parser, this caused silent lesson loss (no PDF, no homework code).
    Captured from real prod-shape output in 2026-04-28 perf bench."""

    def test_real_broken_response_recovers_five_blocks(self):
        """The exact text the LLM returned for 'SS2 Biology: Mitosis' in
        scenario A run 1 — a complete lesson with all 5 sections but no
        outer markers. Should recover all 5 blocks in correct order."""
        pack, raw = parse_lesson_response(BROKEN_LESSON_NO_MARKERS)
        assert pack is not None, "recovery parser should not return None for clean Title-shape text"
        assert len(pack.blocks) == 5
        assert raw == BROKEN_LESSON_NO_MARKERS

        # Positional type assignment matches the system prompt's block order
        types = [type(b).__name__ for b in pack.blocks]
        assert types == [
            "OpenerBlock",
            "ExplainBlock",
            "ActivityBlock",
            "HomeworkBlock",
            "TeacherNotesBlock",
        ]

        # Titles preserved verbatim
        assert pack.blocks[0].title == "Your Body's Secret Duplication Machine"
        assert pack.blocks[1].title == "Unpacking Mitosis: The Cell's Cloning Process"
        assert pack.blocks[4].title == "Teacher Notes"

        # Summary + Details collapsed into body
        assert "Riddle to spark curiosity" in pack.blocks[0].body
        assert "Detective Cell" in pack.blocks[3].body

    def test_single_section_recovers_as_opener(self):
        text = (
            "Title: Solo Lesson\n"
            "Summary: Just one section here\n"
            "Details: A short detail line.\n"
        )
        pack, _ = parse_lesson_response(text)
        assert pack is not None
        assert len(pack.blocks) == 1
        assert type(pack.blocks[0]).__name__ == "OpenerBlock"
        assert pack.blocks[0].title == "Solo Lesson"

    def test_caps_at_five_sections(self):
        """If the LLM emits 7 sections, only the first 5 are kept (matches
        the system prompt's block sequence)."""
        text = "\n\n".join(
            [
                f"Title: Section {i}\nSummary: s{i}\nDetails: d{i}\n"
                for i in range(7)
            ]
        )
        pack, _ = parse_lesson_response(text)
        assert pack is not None
        assert len(pack.blocks) == 5

    def test_real_block_markers_still_take_precedence(self):
        """Recovery must NOT fire when valid [BLOCK_START_X] markers exist —
        otherwise we'd double-process every existing legacy lesson."""
        pack, _ = parse_lesson_response(SAMPLE_LESSON_BLOCKS)
        assert pack is not None
        assert len(pack.blocks) == 5
        # Real blocks expose the actual title verbatim, not a recovery default
        assert pack.blocks[0].title == "What if photosynthesis stopped tomorrow?"

    def test_json_pack_still_takes_precedence(self):
        pack, _ = parse_lesson_response(SAMPLE_LESSON_JSON)
        assert pack is not None
        assert len(pack.blocks) == 5

    def test_plain_prose_returns_none(self):
        """Truly content-free text shouldn't trick the recovery parser."""
        pack, _ = parse_lesson_response("I don't know what subject you mean. Could you clarify?")
        assert pack is None

    def test_clarification_json_not_misclassified(self):
        """The clarification JSON shape from the JSON prompt must NOT be
        recovered as a 1-block lesson (separately handled by parse_clarification)."""
        clar = '{"clarification": "What class level?", "suggestions": ["JSS1", "JSS2"]}'
        pack, _ = parse_lesson_response(clar)
        assert pack is None

    def test_section_with_missing_summary_still_recovers(self):
        """Title + Details only (Summary missing) — should still recover."""
        text = (
            "Title: First Block\n"
            "Details: Only details here.\n"
        )
        pack, _ = parse_lesson_response(text)
        assert pack is not None
        assert len(pack.blocks) == 1
        assert "Only details here" in pack.blocks[0].body

