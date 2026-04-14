"""WhatsApp channel adapter — plain-text summary and block detail for Twilio."""

from __future__ import annotations

from typing import Any

from classgen.core.models import (
    ActivityBlock,
    Block,
    ExplainBlock,
    HomeworkBlock,
    LessonPack,
    OpenerBlock,
    TeacherNotesBlock,
)

from .base import ChannelAdapter

_BLOCK_LABELS: dict[str, str] = {
    "opener": "Hook",
    "explain": "Concept",
    "activity": "Activity",
    "homework": "Homework",
    "teacher_notes": "Notes",
}

_BLOCK_ICONS: dict[str, str] = {
    "opener": "\U0001f3af",
    "explain": "\U0001f4da",
    "activity": "\U0001f3c3",
    "homework": "\U0001f4dd",
    "teacher_notes": "\U0001f4cb",
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

    def render_sections_menu(self, pack: LessonPack) -> str:
        """Numbered section list with navigation hint."""
        topic = pack.meta.topic or "Lesson"
        num_icons = [
            "\u0031\ufe0f\u20e3",
            "\u0032\ufe0f\u20e3",
            "\u0033\ufe0f\u20e3",
            "\u0034\ufe0f\u20e3",
            "\u0035\ufe0f\u20e3",
        ]
        parts = [f"*Your Lesson: {topic}*\n"]
        for i, block in enumerate(pack.blocks):
            label = _BLOCK_LABELS.get(block.type, block.type.replace("_", " ").title())
            icon = num_icons[i] if i < len(num_icons) else f"{i + 1}."
            parts.append(f"  {icon} {label} \u2014 {block.title}")
        parts.append("\nReply with a number (1-5) or name to read.")
        parts.append("'full' for everything, 'pdf' for the PDF link.")
        return "\n".join(parts)

    def render_block_detail(
        self, block: Block, index: int, total: int, blocks: list[Block] | None = None
    ) -> str:
        """Full detail rendering of a single block, tailored by block type."""
        label = _BLOCK_LABELS.get(block.type, block.type.replace("_", " ").title())
        icon = _BLOCK_ICONS.get(block.type, "")
        num = index + 1
        parts = [f"*{num}. {label}: {block.title}* {icon}"]

        if isinstance(block, OpenerBlock):
            meta_parts = []
            if block.duration_minutes:
                meta_parts.append(f"{block.duration_minutes} min")
            if block.format:
                meta_parts.append(f"{block.format} format")
            if meta_parts:
                parts.append(f"_{' \u00b7 '.join(meta_parts)}_")
            parts.append(f"\n{_truncate(block.body, 400)}")
            if block.props:
                parts.append(f"\n*Props:* {', '.join(block.props)}")

        elif isinstance(block, ExplainBlock):
            parts.append(f"\n{_truncate(block.body, 300)}")
            if block.key_terms:
                parts.append("\n*Key Terms:*")
                for kt in block.key_terms[:5]:
                    parts.append(f"\u2022 *{kt.term}* \u2014 {kt.definition}")
            if block.wow_fact:
                parts.append(f"\n\U0001f4a1 _Wow:_ {block.wow_fact}")
            if block.analogy:
                parts.append(f"\U0001f517 _Analogy:_ {block.analogy}")
            if block.equation:
                parts.append(f"\n*Equation:* {block.equation}")

        elif isinstance(block, ActivityBlock):
            meta_parts = []
            if block.duration_minutes:
                meta_parts.append(f"{block.duration_minutes} min")
            if block.group_size:
                meta_parts.append(f"Groups of {block.group_size}")
            if block.format:
                meta_parts.append(f"{block.format} format")
            if meta_parts:
                parts.append(f"_{' \u00b7 '.join(meta_parts)}_")
            parts.append(f"\n{_truncate(block.body, 300)}")
            if block.materials:
                parts.append(f"\n*Materials:* {', '.join(block.materials)}")
            if block.rules:
                parts.append("\n*Rules:*")
                for i, rule in enumerate(block.rules[:5], 1):
                    parts.append(f"{i}. {rule}")
            if block.expected_outcome:
                parts.append(f"\n*Expected:* {block.expected_outcome}")

        elif isinstance(block, HomeworkBlock):
            meta_parts = []
            if block.format:
                meta_parts.append(f"{block.format} format")
            if meta_parts:
                parts.append(f"_{' \u00b7 '.join(meta_parts)}_")
            if block.body:
                parts.append(f"\n{_truncate(block.body, 300)}")
            if block.narrative:
                parts.append(f"\n{_truncate(block.narrative, 200)}")
            if block.tasks:
                parts.append("\n*Tasks:*")
                for task in block.tasks[:5]:
                    parts.append(f"\u2022 {task.instruction}")
            if block.completion:
                parts.append(f"\n*Completion:* {block.completion}")

        elif isinstance(block, TeacherNotesBlock):
            if block.body:
                parts.append(f"\n{_truncate(block.body, 400)}")
            if block.common_mistakes:
                parts.append("\n*Common mistakes:*")
                for m in block.common_mistakes[:5]:
                    parts.append(f"\u2022 {m}")
            if block.quick_assessment:
                parts.append(f"\n*Quick check:* {block.quick_assessment}")
            if block.exam_tip:
                parts.append(f"\n*Exam tip:* {block.exam_tip}")

        # Navigation footer
        all_blocks = blocks or []
        if index < total - 1 and all_blocks:
            next_block = all_blocks[index + 1]
            next_label = _BLOCK_LABELS.get(
                next_block.type, next_block.type.replace("_", " ").title()
            )
            parts.append(f"\n\u25b8 Reply 'next' for {next_label}, or 'sections' to browse.")
        else:
            parts.append("\n\u25b8 Reply 'sections' to browse, or send a new topic.")

        return "\n".join(parts)


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, appending '...' if truncated."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."
