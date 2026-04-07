"""PDF channel adapter — generates PDF from a LessonPack.

Wraps the existing ``generate_pdf_from_markdown`` function by converting
the structured LessonPack back into the Title/Summary/Details text format
that the PDF generator expects. This avoids rewriting the PDF generator
while still benefiting from structured input.
"""

from __future__ import annotations

from typing import Any

from classgen.content.pdf_generator import generate_pdf_from_markdown
from classgen.core.models import Block, LessonPack

from .base import ChannelAdapter


class PDFAdapter(ChannelAdapter):
    """Generates a PDF file from a LessonPack and returns the file path."""

    def render_lesson(
        self,
        pack: LessonPack,
        *,
        homework_code: str | None = None,
        pdf_url: str | None = None,
        base_url: str = "",
        subtitle: str = "",
    ) -> str | None:
        """Render the lesson pack as a PDF. Returns the filename or None on error."""
        text = self._pack_to_text(pack)
        try:
            return generate_pdf_from_markdown(text, subtitle=subtitle)
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None

    def render_block(self, block: Block, index: int, total: int) -> Any:
        return self._block_to_text(block)

    @staticmethod
    def _pack_to_text(pack: LessonPack) -> str:
        """Convert a LessonPack into the Title/Summary/Details text the PDF generator parses."""
        sections = []
        for block in pack.blocks:
            sections.append(PDFAdapter._block_to_text(block))
        return "\n\n".join(sections)

    @staticmethod
    def _block_to_text(block: Block) -> str:
        """Convert a single block to Title/Summary/Details format."""
        # Extract summary-like content based on block type
        fmt: str = getattr(block, "format", "")
        wow: str = getattr(block, "wow_fact", "")
        summary = ""
        if fmt:
            summary = fmt.replace("_", " ").title()
        elif wow:
            summary = wow

        body: str = getattr(block, "body", "") or ""

        # For homework blocks, include narrative if body is empty
        if block.type == "homework" and not body:
            body = getattr(block, "narrative", "") or ""

        parts = [f"Title: {block.title}"]
        if summary:
            parts.append(f"Summary: {summary}")
        parts.append(f"Details: {body}")
        return "\n".join(parts)
