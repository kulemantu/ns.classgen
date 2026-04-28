"""Dual parser for lesson content: JSON (V4.1+) and block markers (legacy).

Provides a single entry point ``parse_lesson_response`` that tries JSON first,
falls back to the ``[BLOCK_START_X]...[BLOCK_END]`` regex format, and always
returns the raw text alongside the parsed result.
"""

from __future__ import annotations

import json
import re

from classgen.content.prompts import BLOCK_PATTERN
from classgen.core.models import (
    ActivityBlock,
    ExplainBlock,
    HomeworkBlock,
    LessonPack,
    OpenerBlock,
    TeacherNotesBlock,
)

# Map old/legacy block type names to canonical model types.
_BLOCK_TYPE_MAP: dict[str, str] = {
    "OPENER": "opener",
    "EXPLAIN": "explain",
    "ACTIVITY": "activity",
    "HOMEWORK": "homework",
    "TEACHER_NOTES": "teacher_notes",
    # Legacy names used in older tests/prompts
    "HOOK": "opener",
    "FACT": "explain",
    "APPLICATION": "activity",
}

# Map canonical type string to the correct block model class.
_BLOCK_CLASS_MAP = {
    "opener": OpenerBlock,
    "explain": ExplainBlock,
    "activity": ActivityBlock,
    "homework": HomeworkBlock,
    "teacher_notes": TeacherNotesBlock,
}

# Regex for extracting Title / Summary / Details within a block body.
_FIELD_RE = re.compile(
    r"Title:\s*\*{0,2}(.*?)\*{0,2}\s*\n"
    r"(?:Summary:\s*(.*?)\n)?"
    r"(?:Details:\s*([\s\S]*))?",
    re.DOTALL,
)


def parse_lesson_json(raw: str) -> LessonPack | None:
    """Parse a JSON string into a LessonPack. Returns None on failure."""
    text = raw.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    try:
        return LessonPack.model_validate(data)
    except Exception:
        return None


def parse_lesson_blocks(raw: str) -> LessonPack | None:
    """Parse legacy ``[BLOCK_START_X]...[BLOCK_END]`` text into a LessonPack.

    Maps old block names (HOOK, FACT, APPLICATION) to their canonical types.
    Collapses Summary + Details into the ``body`` field.
    Returns None if no blocks are found.
    """
    matches = BLOCK_PATTERN.findall(raw)
    if not matches:
        return None

    blocks = []
    for block_type_raw, block_body in matches:
        canonical = _BLOCK_TYPE_MAP.get(block_type_raw.upper())
        if not canonical:
            continue

        cls = _BLOCK_CLASS_MAP.get(canonical)
        if not cls:
            continue

        # Parse Title / Summary / Details from the block body
        field_match = _FIELD_RE.search(block_body.strip())
        if field_match:
            title = field_match.group(1).strip()
            summary = (field_match.group(2) or "").strip()
            details = (field_match.group(3) or "").strip()
            body = f"{summary}\n\n{details}".strip() if summary else details
        else:
            # No Title/Summary/Details structure — use whole body
            title = canonical.replace("_", " ").title()
            body = block_body.strip()

        blocks.append(cls(title=title, body=body))

    if not blocks:
        return None

    return LessonPack(blocks=blocks)


def parse_clarification(raw: str) -> tuple[str, list[str]] | None:
    """Detect and parse a clarification JSON response from the LLM.

    The V4.1 JSON system prompt instructs the LLM to request missing context as:
        {"clarification": "Your question here", "suggestions": ["A", "B", "C"]}

    Returns ``(question, suggestions)`` or ``None`` if the input is not a
    clarification (e.g. a full lesson pack, plain text, or malformed JSON).
    """
    text = raw.strip()

    # Strip markdown code fences if present (mirrors parse_lesson_json)
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    question = data.get("clarification")
    if not isinstance(question, str) or not question.strip():
        return None

    raw_suggestions = data.get("suggestions") or []
    if not isinstance(raw_suggestions, list):
        raw_suggestions = []
    suggestions = [s.strip() for s in raw_suggestions if isinstance(s, str) and s.strip()]

    return question.strip(), suggestions


def parse_lesson_response(raw: str) -> tuple[LessonPack | None, str]:
    """Try JSON first, fall back to block markers.

    Returns ``(lesson_pack, raw_text)``. The raw text is always preserved
    for backward compatibility and storage.
    """
    # Try structured JSON
    pack = parse_lesson_json(raw)
    if pack and pack.blocks:
        return pack, raw

    # Fall back to legacy block markers
    pack = parse_lesson_blocks(raw)
    return pack, raw
