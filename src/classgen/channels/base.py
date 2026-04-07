"""Abstract base class for channel adapters.

Each adapter transforms a LessonPack into the format appropriate for
its delivery channel (web, WhatsApp, PDF, homework page).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from classgen.core.models import Block, LessonPack


class ChannelAdapter(ABC):
    """Renders a LessonPack into a channel-specific output format."""

    @abstractmethod
    def render_lesson(
        self,
        pack: LessonPack,
        *,
        homework_code: str | None = None,
        pdf_url: str | None = None,
        base_url: str = "",
    ) -> Any:
        """Render a full lesson pack for the channel."""

    @abstractmethod
    def render_block(self, block: Block, index: int, total: int) -> Any:
        """Render a single block (used by SSE streaming)."""
