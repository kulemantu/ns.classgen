"""Dual parser for lesson content: JSON (V4.1+) and block markers (legacy).

Provides a single entry point ``parse_lesson_response`` that tries JSON first,
falls back to the ``[BLOCK_START_X]...[BLOCK_END]`` regex format, and always
returns the raw text alongside the parsed result.
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from classgen.content.prompts import BLOCK_PATTERN
from classgen.core.models import (
    ActivityBlock,
    ExplainBlock,
    HomeworkBlock,
    LessonMeta,
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

# Recovery parser positional types — when [BLOCK_START_X] markers are missing,
# we fall back to assigning sections by order matching the system prompt's
# 5-block structure.
_RECOVERY_BLOCK_TYPES = ["opener", "explain", "activity", "homework", "teacher_notes"]
_TITLE_LINE_RE = re.compile(r"^Title:\s*", re.MULTILINE)


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
    except ValidationError:
        # One bad block would otherwise reject the whole pack — try to keep
        # the good ones. See _salvage_lesson_json for the per-block recovery.
        return _salvage_lesson_json(data)
    except Exception:
        return None


def _salvage_lesson_json(data: dict) -> LessonPack | None:
    """Best-effort per-block recovery when full LessonPack validation fails.

    Validates each block independently against its concrete class. Drops only
    the bad ones. Returns ``None`` if no block survives, so callers can fall
    through to the legacy block-marker / no-markers parsers.
    """
    blocks_raw = data.get("blocks")
    if not isinstance(blocks_raw, list):
        return None

    survivors: list = []
    dropped = 0
    for block in blocks_raw:
        if not isinstance(block, dict):
            dropped += 1
            continue
        cls = _BLOCK_CLASS_MAP.get(block.get("type", ""))
        if not cls:
            dropped += 1
            continue
        try:
            survivors.append(cls.model_validate(block))
        except ValidationError:
            dropped += 1

    if not survivors:
        return None

    # Surfaces in production logs so we can monitor salvage frequency.
    print(
        f"[salvage] dropped {dropped} invalid block(s), kept {len(survivors)}",
        flush=True,
    )

    meta_raw = data.get("meta")
    try:
        meta = LessonMeta.model_validate(meta_raw) if isinstance(meta_raw, dict) else LessonMeta()
    except ValidationError:
        meta = LessonMeta()

    return LessonPack(
        version=data.get("version", "4.0"),
        meta=meta,
        blocks=survivors,
    )


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


def _recover_blocks_no_markers(raw: str) -> LessonPack | None:
    """Recover a LessonPack when the LLM emitted ``Title:/Summary:/Details:``
    triples but dropped the surrounding ``[BLOCK_START_X]...[BLOCK_END]``
    markers. Used as a last-resort fallback in ``parse_lesson_response``.

    Splits the text on each ``Title:`` line and treats the resulting sections
    as blocks in positional order matching the system prompt's block sequence
    (opener, explain, activity, homework, teacher_notes). Caps at 5 sections;
    returns ``None`` if no valid section is found.
    """
    title_positions = [m.start() for m in _TITLE_LINE_RE.finditer(raw)]
    if not title_positions:
        return None

    title_positions.append(len(raw))
    blocks = []
    for i, start in enumerate(title_positions[:-1]):
        if i >= len(_RECOVERY_BLOCK_TYPES):
            break
        section = raw[start : title_positions[i + 1]].strip()
        field_match = _FIELD_RE.search(section)
        if not field_match:
            continue
        title = field_match.group(1).strip()
        summary = (field_match.group(2) or "").strip()
        details = (field_match.group(3) or "").strip()
        body = f"{summary}\n\n{details}".strip() if summary else details
        if not title:
            continue
        cls = _BLOCK_CLASS_MAP[_RECOVERY_BLOCK_TYPES[i]]
        blocks.append(cls(title=title, body=body))

    if not blocks:
        return None

    # Surfaces in production logs so we can monitor recovery frequency.
    print(f"[recovery] no-markers fallback fired blocks={len(blocks)}", flush=True)
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
    """Try JSON first, fall back to block markers, last-resort recover from
    no-markers Title/Summary/Details text.

    Returns ``(lesson_pack, raw_text)``. The raw text is always preserved
    for backward compatibility and storage.
    """
    # Try structured JSON
    pack = parse_lesson_json(raw)
    if pack and pack.blocks:
        return pack, raw

    # Fall back to legacy block markers
    pack = parse_lesson_blocks(raw)
    if pack:
        return pack, raw

    # Last resort: LLM dropped the [BLOCK_START_X] markers but kept the
    # Title:/Summary:/Details: structure. Recover positionally.
    pack = _recover_blocks_no_markers(raw)
    return pack, raw
