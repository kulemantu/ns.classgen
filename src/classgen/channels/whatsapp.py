"""WhatsApp channel adapter — plain-text summary for Twilio."""

from __future__ import annotations

from typing import Any

from classgen.core.models import Block, LessonPack

from .base import ChannelAdapter

_BLOCK_LABELS: dict[str, str] = {
    "opener": "Hook",
    "explain": "Concept",
    "activity": "Activity",
    "homework": "Homework",
    "teacher_notes": "Notes",
}


class WhatsAppAdapter(ChannelAdapter):
    """Produces a WhatsApp-friendly plain-text summary from a LessonPack.

    Output matches the format of the legacy ``_whatsapp_summary()`` function:
    block labels + titles, homework code link, PDF note.
    """

    def render_lesson(
        self,
        pack: LessonPack,
        *,
        homework_code: str | None = None,
        pdf_url: str | None = None,
        base_url: str = "",
    ) -> str:
        parts = ["*ClassGen Lesson Pack*\n"]

        for block in pack.blocks:
            label = _BLOCK_LABELS.get(block.type, block.type.replace("_", " ").title())
            parts.append(f"  *{label}:* {block.title}")

        if homework_code:
            parts.append(f"\n*Homework Code:* {homework_code}")
            parts.append(f"Students visit: {base_url}/h/{homework_code}")

        parts.append("\nFull lesson plan attached as PDF.")
        return "\n".join(parts)

    def render_block(self, block: Block, index: int, total: int) -> Any:
        label = _BLOCK_LABELS.get(block.type, block.type.replace("_", " ").title())
        return f"*{label}:* {block.title}"
