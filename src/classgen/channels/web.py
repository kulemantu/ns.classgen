"""Web channel adapter — returns structured dicts for the frontend."""

from __future__ import annotations

from typing import Any

from classgen.core.models import Block, LessonPack

from .base import ChannelAdapter


class WebAdapter(ChannelAdapter):
    """Returns the LessonPack as a serializable dict.

    The frontend renders blocks as rich cards from the structured data.
    """

    def render_lesson(
        self,
        pack: LessonPack,
        *,
        homework_code: str | None = None,
        pdf_url: str | None = None,
        base_url: str = "",
    ) -> dict[str, Any]:
        result: dict[str, Any] = pack.model_dump()
        result["homework_code"] = homework_code
        result["pdf_url"] = pdf_url
        return result

    def render_block(self, block: Block, index: int, total: int) -> dict[str, Any]:
        return block.model_dump()
