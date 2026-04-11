"""Tests for classgen.channels — channel adapter rendering."""

import os

from classgen.channels import PDFAdapter, WebAdapter, WhatsAppAdapter, get_adapter
from classgen.core.models import LessonPack
from tests.fixtures import SAMPLE_LESSON_JSON_DICT


def _make_pack() -> LessonPack:
    return LessonPack.model_validate(SAMPLE_LESSON_JSON_DICT)


class TestWebAdapter:
    def test_returns_dict(self):
        adapter = WebAdapter()
        result = adapter.render_lesson(
            _make_pack(), homework_code="TEST42", pdf_url="/static/test.pdf"
        )
        assert isinstance(result, dict)
        assert result["homework_code"] == "TEST42"
        assert result["pdf_url"] == "/static/test.pdf"

    def test_contains_blocks(self):
        adapter = WebAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "blocks" in result
        assert len(result["blocks"]) == 5
        assert result["blocks"][0]["type"] == "opener"

    def test_contains_meta(self):
        adapter = WebAdapter()
        result = adapter.render_lesson(_make_pack())
        assert result["meta"]["subject"] == "Biology"

    def test_render_block(self):
        adapter = WebAdapter()
        pack = _make_pack()
        block_dict = adapter.render_block(pack.blocks[0], index=0, total=5)
        assert isinstance(block_dict, dict)
        assert block_dict["type"] == "opener"
        assert "title" in block_dict


class TestWhatsAppAdapter:
    def test_output_under_1500_chars(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(
            _make_pack(), homework_code="BIO42", base_url="https://classgen.ng"
        )
        assert len(result) < 1500

    def test_correct_labels(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "*Hook:*" in result
        assert "*Concept:*" in result
        assert "*Activity:*" in result
        assert "*Homework:*" in result
        assert "*Notes:*" in result

    def test_homework_code_included(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(
            _make_pack(), homework_code="BIO42", base_url="https://classgen.ng"
        )
        assert "BIO42" in result
        assert "https://classgen.ng/h/BIO42" in result

    def test_no_homework_code(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "Homework Code:" not in result

    def test_header_present(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "*ClassGen Lesson Pack*" in result

    def test_pdf_note(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "Full lesson plan attached as PDF." in result

    def test_block_titles_present(self):
        adapter = WhatsAppAdapter()
        result = adapter.render_lesson(_make_pack())
        assert "What if photosynthesis stopped tomorrow?" in result
        assert "The Factory Inside Every Leaf" in result

    def test_render_block(self):
        adapter = WhatsAppAdapter()
        pack = _make_pack()
        text = adapter.render_block(pack.blocks[0], index=0, total=5)
        assert "*Hook:*" in text


class TestPDFAdapter:
    def setup_method(self):
        self._created_files: list[str] = []

    def teardown_method(self):
        for f in self._created_files:
            if os.path.exists(f):
                os.remove(f)

    def test_generates_file(self):
        adapter = PDFAdapter()
        filename = adapter.render_lesson(_make_pack(), subtitle="Test lesson")
        assert filename is not None
        assert filename.endswith(".pdf")
        # Track for cleanup
        static_path = os.path.join("static", filename)
        self._created_files.append(static_path)
        assert os.path.exists(static_path)

    def test_pack_to_text_format(self):
        text = PDFAdapter._pack_to_text(_make_pack())
        assert "Title:" in text
        assert "Details:" in text

    def test_render_block_returns_text(self):
        adapter = PDFAdapter()
        pack = _make_pack()
        text = adapter.render_block(pack.blocks[0], index=0, total=5)
        assert "Title:" in text


class TestGetAdapter:
    def test_web(self):
        assert isinstance(get_adapter("web"), WebAdapter)

    def test_whatsapp(self):
        assert isinstance(get_adapter("whatsapp"), WhatsAppAdapter)

    def test_pdf(self):
        assert isinstance(get_adapter("pdf"), PDFAdapter)

    def test_unknown_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown channel"):
            get_adapter("sms")
