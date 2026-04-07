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
    parse_lesson_blocks,
    parse_lesson_json,
    parse_lesson_response,
)
from tests.fixtures import (
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
            "[BLOCK_START_OPENER]\n"
            "Just some raw text without the expected structure.\n"
            "[BLOCK_END]"
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
