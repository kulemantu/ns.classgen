"""Security-focused tests for PDF generation.

Verifies that the PDF pipeline handles adversarial and edge-case input
without crashing: Unicode outside latin-1, markdown image injection,
block marker remnants, and very long content.
"""

from __future__ import annotations

import glob as globmod
import os

from classgen.api.chat import (
    _clean_block_markers_for_pdf,
    _strip_images_for_pdf,
)
from classgen.content.pdf_generator import (
    _sanitize_for_latin1,
    generate_pdf_from_markdown,
)

# Resolve static dir the same way the PDF generator does
_STATIC_DIR = os.environ.get(
    "STATIC_DIR",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static",
    ),
)


def _cleanup_pdfs():
    """Remove any PDFs generated during tests."""
    for f in globmod.glob(os.path.join(_STATIC_DIR, "lesson_plan_*.pdf")):
        try:
            os.remove(f)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# _sanitize_for_latin1
# ---------------------------------------------------------------------------


class TestSanitizeForLatin1:
    """The sanitizer must *replace* (not silently strip) known special chars,
    and must never raise on unknown Unicode."""

    def test_degree_symbol_replaced(self):
        """Degree sign (U+00B0) is replaced with ' deg', not stripped."""
        result = _sanitize_for_latin1("Water boils at 100\u00b0C")
        assert "deg" in result
        assert "\u00b0" not in result

    def test_naira_sign_replaced(self):
        """Naira sign (U+20A6) is replaced with 'NGN'."""
        result = _sanitize_for_latin1("Price: \u20a61500")
        assert "NGN" in result
        assert "\u20a6" not in result

    def test_right_arrow_replaced(self):
        """Right arrow (U+2192) becomes '->'."""
        result = _sanitize_for_latin1("Step 1 \u2192 Step 2")
        assert "->" in result
        assert "\u2192" not in result

    def test_pi_replaced(self):
        """Greek pi (U+03C0) becomes 'pi'."""
        result = _sanitize_for_latin1("Area = \u03c0r\u00b2")
        assert "pi" in result
        assert "\u03c0" not in result

    def test_em_dash_replaced(self):
        """Em dash (U+2014) becomes '-'."""
        result = _sanitize_for_latin1("word\u2014another")
        assert "-" in result
        assert "\u2014" not in result

    def test_smart_quotes_replaced(self):
        """Smart quotes are replaced with ASCII equivalents."""
        result = _sanitize_for_latin1("\u201cHello\u201d and \u2018world\u2019")
        assert '"Hello"' in result
        assert "'world'" in result

    def test_subscript_digits(self):
        """Chemical formula subscripts (H\u2082O) are replaced with digits."""
        result = _sanitize_for_latin1("H\u2082O")
        assert "H2O" in result

    def test_superscript_digits(self):
        """Exponents like x\u00b2 are replaced with digits."""
        result = _sanitize_for_latin1("x\u00b2 + y\u00b3")
        assert "x2" in result
        assert "y3" in result

    def test_emoji_does_not_crash(self):
        """Emoji (outside latin-1) are stripped but must not raise."""
        result = _sanitize_for_latin1("Great job! \U0001f44d\U0001f389")
        assert "Great job!" in result
        # Emoji should be gone (latin-1 encode ignores them)
        assert "\U0001f44d" not in result

    def test_cjk_does_not_crash(self):
        """CJK characters are outside latin-1 and should be dropped silently."""
        result = _sanitize_for_latin1("Test \u4e16\u754c data")
        assert "Test" in result
        assert "data" in result

    def test_mixed_replacements_and_fallback(self):
        """A mix of known replacements and unknown Unicode is handled."""
        text = "Temp: 37\u00b0C \u2192 fever \U0001f321"
        result = _sanitize_for_latin1(text)
        assert "deg" in result
        assert "->" in result
        # Thermometer emoji stripped
        assert "\U0001f321" not in result

    def test_plain_ascii_unchanged(self):
        """Plain ASCII text passes through untouched."""
        text = "Hello, World! 123 #$%"
        assert _sanitize_for_latin1(text) == text


# ---------------------------------------------------------------------------
# _strip_images_for_pdf
# ---------------------------------------------------------------------------


class TestStripImagesForPdf:
    """Markdown images and data URIs must be stripped to prevent FPDF crashes
    and potential content injection."""

    def test_markdown_image_removed(self):
        """Standard markdown image syntax is fully removed."""
        text = "Before ![diagram](https://evil.com/img.png) After"
        result = _strip_images_for_pdf(text)
        assert "![" not in result
        assert "evil.com" not in result
        assert "Before" in result
        assert "After" in result

    def test_data_uri_removed(self):
        """Base64 data:image URIs are stripped."""
        text = "See: data:image/png;base64,iVBORw0KGgo= end"
        result = _strip_images_for_pdf(text)
        assert "data:image" not in result
        assert "end" in result

    def test_multiple_images_removed(self):
        """Multiple markdown images in one text are all stripped."""
        text = "![a](http://x.com/1.png) text ![b](http://y.com/2.png)"
        result = _strip_images_for_pdf(text)
        assert "![" not in result
        assert "x.com" not in result
        assert "y.com" not in result
        assert "text" in result

    def test_no_images_unchanged(self):
        """Text without images passes through untouched."""
        text = "Normal text with [link](url) and **bold**"
        result = _strip_images_for_pdf(text)
        assert result == text


# ---------------------------------------------------------------------------
# _clean_block_markers_for_pdf
# ---------------------------------------------------------------------------


class TestCleanBlockMarkers:
    """Block markers from the LLM response must be fully stripped before
    the content reaches the PDF renderer."""

    def test_block_start_removed(self):
        """[BLOCK_START_X] markers are stripped."""
        text = "[BLOCK_START_OPENER]\nTitle: Hook\n[BLOCK_END]"
        result = _clean_block_markers_for_pdf(text)
        assert "[BLOCK_START" not in result
        assert "[BLOCK_END]" not in result
        assert "Title: Hook" in result

    def test_all_block_types_removed(self):
        """All five block types are cleaned."""
        types = ["OPENER", "EXPLAIN", "ACTIVITY", "HOMEWORK", "TEACHER_NOTES"]
        text = "\n".join(f"[BLOCK_START_{t}]\nTitle: {t}\n[BLOCK_END]" for t in types)
        result = _clean_block_markers_for_pdf(text)
        for t in types:
            assert f"[BLOCK_START_{t}]" not in result
        assert "[BLOCK_END]" not in result

    def test_images_also_stripped(self):
        """_clean_block_markers_for_pdf also strips images (calls _strip_images)."""
        text = "[BLOCK_START_OPENER]\n![img](url)\n[BLOCK_END]"
        result = _clean_block_markers_for_pdf(text)
        assert "![" not in result

    def test_excessive_newlines_collapsed(self):
        """Three or more consecutive newlines are collapsed to two."""
        text = "[BLOCK_START_A]\n\n\n\n\n[BLOCK_END]\n[BLOCK_START_B]\nText\n[BLOCK_END]"
        result = _clean_block_markers_for_pdf(text)
        assert "\n\n\n" not in result


# ---------------------------------------------------------------------------
# generate_pdf_from_markdown (integration)
# ---------------------------------------------------------------------------


class TestGeneratePdf:
    """End-to-end PDF generation from markdown text."""

    def teardown_method(self):
        _cleanup_pdfs()

    def test_basic_generation(self):
        """A simple markdown string produces a valid PDF file."""
        filename = generate_pdf_from_markdown("**Title**\n\nSome content.")
        assert filename.endswith(".pdf")
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_block_structured_content(self):
        """Block-structured lesson content generates a PDF with sections."""
        content = (
            "Title: **Photosynthesis**\n"
            "Summary: Plants make food from sunlight.\n"
            "Details: Chloroplasts absorb light energy.\n\n"
            "Title: **Respiration**\n"
            "Summary: Cells release energy.\n"
            "Details: Mitochondria break down glucose.\n"
        )
        filename = generate_pdf_from_markdown(content, subtitle="Biology")
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_unicode_content_does_not_crash(self):
        """Content with mixed Unicode generates a PDF without errors."""
        text = (
            "Temperature: 37\u00b0C \u2192 fever\n"
            "Cost: \u20a61500\n"
            "\u03c0 = 3.14\n"
            "H\u2082O is water\n"
            "Emoji: \U0001f4da\n"
        )
        filename = generate_pdf_from_markdown(text)
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)

    def test_very_long_text_does_not_crash(self):
        """A very long document (many pages) generates without error."""
        long_text = "This is a long paragraph. " * 500
        filename = generate_pdf_from_markdown(long_text)
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000

    def test_empty_text(self):
        """An empty string still produces a valid (header-only) PDF."""
        filename = generate_pdf_from_markdown("")
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)

    def test_school_name_in_header(self):
        """Passing school_name customizes the PDF header."""
        filename = generate_pdf_from_markdown("Content", school_name="Lagos Grammar School")
        path = os.path.join(_STATIC_DIR, filename)
        assert os.path.exists(path)
