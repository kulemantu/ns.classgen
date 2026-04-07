"""Web chat API router -- POST /api/chat and lesson generation helpers."""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from classgen.api.schemas import ChatRequest
from classgen.channels.pdf import PDFAdapter
from classgen.commands.router import handle_command
from classgen.content.pdf_generator import generate_pdf_from_markdown
from classgen.content.prompts import (
    CLASSGEN_JSON_SYSTEM_PROMPT,
    CLASSGEN_SYSTEM_PROMPT,
    QUIZ_GENERATION_PROMPT,
)
from classgen.core.feature_flags import flags
from classgen.core.models import HomeworkBlock, LessonPack
from classgen.core.parsers import parse_lesson_response
from classgen.data import (
    cache_lesson,
    get_cached_lesson,
    get_session_history,
    get_teacher_by_phone,
    log_lesson_generated,
    log_session,
    save_homework_code,
)
from classgen.data.lessons import get_cached_lesson_json
from classgen.data.subscriptions import log_usage
from classgen.services.billing_service import check_usage
from classgen.services.llm import (
    call_openrouter,
    call_openrouter_json,
    generate_homework_code,
    stream_openrouter,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_content(text: str, pack: LessonPack | None) -> bool:
    """Check if a response contains lesson content (blocks or structured)."""
    return _has_lesson_blocks(text) or (
        pack is not None and len(pack.blocks) > 0
    )


def _strip_images_for_pdf(text: str) -> str:
    """Strip markdown images and base64 data URLs to prevent FPDF crashes."""
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text, flags=re.DOTALL)
    text = re.sub(r'data:image.*?(?=["\'\)\s])', "", text)
    return text


def _has_lesson_blocks(text: str) -> bool:
    """Check if the response contains structured lesson blocks.

    Returns False for clarifying questions without blocks.
    """
    return bool(re.search(r"\[BLOCK_START_", text))


def _clean_block_markers_for_pdf(text: str) -> str:
    """Strip block markers and format for readable PDF output."""
    text = re.sub(r"\[BLOCK_START_\w+\]", "", text)
    text = re.sub(r"\[BLOCK_END\]", "\n", text)
    text = _strip_images_for_pdf(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_homework_block(text: str) -> str:
    """Extract the HOMEWORK block content from a lesson response."""
    match = re.search(r"\[BLOCK_START_HOMEWORK\](.*?)\[BLOCK_END\]", text, re.DOTALL)
    return match.group(1).strip() if match else ""


async def _generate_quiz_questions(lesson_content: str) -> list:
    """Generate 5 MCQ questions from lesson content via a second LLM call."""
    try:
        raw = await call_openrouter(QUIZ_GENERATION_PROMPT, lesson_content)
        if not raw:
            return []
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) > 0:
            return questions[:5]
    except Exception as e:
        print(f"Error generating quiz: {e}")
    return []


def _parse_lesson_request(msg: str) -> tuple[str, str, str]:
    """Best-effort parse of 'SS2 Biology: Photosynthesis'.

    Returns (class_level, subject, topic).
    """
    m = re.match(r"(SS\d|JSS\d)\s+(\w+)[:\s]+(.+)", msg.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2).strip(), m.group(3).strip()
    return "", "", ""


async def _generate_lesson(
    user_message: str,
    thread_id: str,
    limit: int = 10,
    teacher_phone: str = "",
) -> tuple[str, str | None, str | None, LessonPack | None]:
    """Shared logic: log input, call LLM, generate PDF + homework code, log output.

    Returns (reply, pdf_url, homework_code, lesson_pack).
    """
    # Check content cache before spending LLM tokens
    class_level, subject, topic = _parse_lesson_request(user_message)
    if class_level and subject and topic:
        cached = get_cached_lesson(subject, topic, class_level)
        if cached:
            print(f"[cache hit] {class_level} {subject}: {topic}")
            log_session(thread_id, "user", user_message)
            log_session(thread_id, "assistant", cached)
            # Try to load structured JSON from cache
            cached_json = (
                get_cached_lesson_json(subject, topic, class_level)
                if flags.structured_output else None
            )
            cached_pack = None
            if cached_json:
                cached_pack, _ = parse_lesson_response(json.dumps(cached_json))
            if not cached_pack:
                cached_pack, _ = parse_lesson_response(cached)
            return await _finalize_lesson(
                cached,
                user_message,
                thread_id,
                teacher_phone,
                class_level,
                subject,
                topic,
                lesson_pack=cached_pack,
            )

    # Fetch history BEFORE logging the new message (avoids duplicate in LLM context)
    history = get_session_history(thread_id, limit=limit)
    log_session(thread_id, "user", user_message)

    history_context = (
        "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        if history
        else "No previous context."
    )

    prompt = (
        f"Previous Conversation Context:\n{history_context}"
        f"\n\nTeacher's message:\n{user_message}"
    )

    # Branch: structured JSON or legacy text blocks
    if flags.structured_output:
        assistant_reply = await call_openrouter_json(CLASSGEN_JSON_SYSTEM_PROMPT, prompt)
    else:
        assistant_reply = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, prompt)

    if not assistant_reply:
        return (
            "I'm sorry, my AI engine is currently resting. Please try again soon.",
            None,
            None,
            None,
        )

    log_session(thread_id, "assistant", assistant_reply)

    # Parse response (JSON first, block fallback)
    lesson_pack, _ = parse_lesson_response(assistant_reply)

    # Cache if this was a parseable lesson request
    has_blocks = _has_content(assistant_reply, lesson_pack)
    if class_level and subject and topic and has_blocks:
        cache_lesson(
            subject, topic, class_level, assistant_reply,
            lesson_json=lesson_pack.model_dump() if lesson_pack else None,
        )

    return await _finalize_lesson(
        assistant_reply,
        user_message,
        thread_id,
        teacher_phone,
        class_level,
        subject,
        topic,
        lesson_pack=lesson_pack,
    )


async def _finalize_lesson(
    assistant_reply: str,
    user_message: str,
    thread_id: str,
    teacher_phone: str,
    class_level: str,
    subject: str,
    topic: str,
    lesson_pack: LessonPack | None = None,
) -> tuple[str, str | None, str | None, LessonPack | None]:
    """Generate PDF, homework code, log history. Shared by cache-hit and fresh paths."""
    pdf_url = None
    homework_code = None
    has_content = _has_content(assistant_reply, lesson_pack)

    if has_content:
        # --- PDF generation ---
        try:
            if lesson_pack and flags.structured_output:
                pdf_adapter = PDFAdapter()
                pdf_filename = pdf_adapter.render_lesson(
                    lesson_pack, subtitle=user_message[:120]
                )
            else:
                pdf_text = _clean_block_markers_for_pdf(assistant_reply)
                pdf_filename = generate_pdf_from_markdown(
                    pdf_text, subtitle=user_message[:120]
                )
            pdf_url = f"/static/{pdf_filename}" if pdf_filename else None
        except Exception as e:
            print(f"Error generating PDF: {e}")

        # --- Homework code + quiz ---
        try:
            homework_code = generate_homework_code()
            homework_block_text = _extract_homework_block(assistant_reply)

            # When structured output + embedded quiz: extract quiz from LessonPack
            quiz_questions: list = []
            if flags.effective_embedded_quiz and lesson_pack:
                hw_block = next(
                    (b for b in lesson_pack.blocks if isinstance(b, HomeworkBlock)),
                    None,
                )
                if hw_block and hw_block.quiz:
                    quiz_questions = [q.model_dump() for q in hw_block.quiz]
                    if not homework_block_text and hw_block.narrative:
                        homework_block_text = hw_block.narrative

            # Fall back to second LLM call for quiz
            if not quiz_questions:
                quiz_questions = await _generate_quiz_questions(assistant_reply)

            save_homework_code(
                homework_code,
                thread_id,
                assistant_reply,
                quiz_questions,
                homework_block_text,
                teacher_phone=teacher_phone,
                lesson_json=(
                    lesson_pack.model_dump()
                    if (lesson_pack and flags.structured_output) else None
                ),
            )
        except Exception as e:
            print(f"Error generating homework code: {e}")
            homework_code = None

        # Log to lesson history for curriculum tracking
        if teacher_phone and class_level and subject and topic:
            log_lesson_generated(teacher_phone, subject, topic, class_level)

    return assistant_reply, pdf_url, homework_code, lesson_pack


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/api/chat")
async def local_chat_endpoint(req: ChatRequest, request: Request):
    """Local JSON endpoint for the web UI."""
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Link lessons to registered web teachers for stats tracking
    teacher = get_teacher_by_phone(req.thread_id)
    teacher_phone = req.thread_id if teacher else ""

    # Handle commands (with proper base_url for link generation)
    cmd_result = handle_command(req.message, req.thread_id, base_url)
    if cmd_result:
        # Study mode: send topic to LLM with a recap prompt
        if cmd_result.session_action == "study":
            topic = cmd_result.new_thread_id or req.message
            study_prompt = (
                "Give a concise study recap of this topic"
                " for a secondary school student. "
                "Include: key definitions, the main "
                "formula/rule, one example, and 3 quick "
                "self-test questions. Keep it under "
                "1000 characters. Topic: " + topic
            )
            recap = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, study_prompt)
            return {
                "reply": recap or "Could not generate a recap right now. Try again.",
                "pdf_url": None,
                "homework_code": None,
            }
        return {"reply": cmd_result.reply, "pdf_url": None, "homework_code": None}

    # Check usage quota (same enforcement as WhatsApp)
    if teacher_phone:
        usage = check_usage(teacher_phone)
        if not usage.allowed:
            return {"reply": usage.message, "pdf_url": None, "homework_code": None}

    assistant_reply, pdf_url, homework_code, lesson_pack = await _generate_lesson(
        req.message, req.thread_id, teacher_phone=teacher_phone
    )

    # Track usage for registered teachers
    has_content = _has_content(assistant_reply, lesson_pack)
    if teacher_phone and has_content:
        log_usage(teacher_phone, "lesson")

    response: dict = {
        "reply": assistant_reply,
        "pdf_url": pdf_url,
        "homework_code": homework_code,
    }

    # When structured output is on, include the lesson pack for the frontend
    if lesson_pack and flags.structured_output:
        response["lesson_pack"] = lesson_pack.model_dump()

    return response


# ---------------------------------------------------------------------------
# SSE Streaming
# ---------------------------------------------------------------------------


class JSONBlockAccumulator:
    """Accumulates streaming tokens and detects complete JSON blocks.

    Watches for complete objects inside a ``"blocks": [...]`` array by
    tracking brace depth. Each completed block is yielded as a dict.
    """

    def __init__(self) -> None:
        self.buffer = ""
        self._in_blocks = False
        self._block_start = -1
        self._depth = 0
        self.blocks_emitted: list[dict] = []

    def feed(self, token: str) -> list[dict]:
        """Feed a token. Returns list of newly completed blocks."""
        completed = []
        for ch in token:
            self.buffer += ch

            # Detect entry into the blocks array
            if not self._in_blocks:
                if self.buffer.endswith('"blocks"'):
                    self._in_blocks = True
                continue

            # Track brace depth within the blocks array
            if ch == "{":
                if self._depth == 0:
                    self._block_start = len(self.buffer) - 1
                self._depth += 1
            elif ch == "}":
                self._depth -= 1
                if self._depth == 0 and self._block_start >= 0:
                    block_str = self.buffer[self._block_start:]
                    try:
                        block = json.loads(block_str)
                        if isinstance(block, dict) and "type" in block:
                            completed.append(block)
                            self.blocks_emitted.append(block)
                    except json.JSONDecodeError:
                        pass
                    # Trim buffer to free memory from emitted blocks
                    self.buffer = ""
                    self._block_start = -1

        return completed


def _sse_event(event: str, data: dict | str) -> str:
    """Format an SSE event string.

    Event names are sanitized to prevent SSE frame injection via newlines.
    Data is always JSON-serialized to ensure safe multi-line handling.
    """
    safe_event = event.replace("\n", "").replace("\r", "")
    payload = json.dumps(data) if isinstance(data, dict) else json.dumps(data)
    return f"event: {safe_event}\ndata: {payload}\n\n"


@router.post("/api/chat/stream")
async def stream_chat_endpoint(req: ChatRequest, request: Request):
    """SSE streaming endpoint for the web UI.

    When ``FF_SSE_STREAMING`` is off, falls back to the blocking JSON
    response from the standard endpoint.
    """
    if not flags.effective_sse_streaming:
        result = await local_chat_endpoint(req, request)
        return result

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    teacher = get_teacher_by_phone(req.thread_id)
    teacher_phone = req.thread_id if teacher else ""

    # Handle commands normally (not streamed)
    cmd_result = handle_command(req.message, req.thread_id, base_url)
    if cmd_result:
        if cmd_result.session_action == "study":
            topic = cmd_result.new_thread_id or req.message
            study_prompt = (
                "Give a concise study recap of this topic"
                " for a secondary school student. "
                "Include: key definitions, the main "
                "formula/rule, one example, and 3 quick "
                "self-test questions. Keep it under "
                "1000 characters. Topic: " + topic
            )
            recap = await call_openrouter(
                CLASSGEN_SYSTEM_PROMPT, study_prompt
            )
            return {
                "reply": recap or "Could not generate.",
                "pdf_url": None,
                "homework_code": None,
            }
        return {
            "reply": cmd_result.reply,
            "pdf_url": None,
            "homework_code": None,
        }

    # Usage check
    if teacher_phone:
        usage = check_usage(teacher_phone)
        if not usage.allowed:
            return {
                "reply": usage.message,
                "pdf_url": None,
                "homework_code": None,
            }

    async def event_stream():
        # Send meta immediately from request parsing
        class_level, subject, topic = _parse_lesson_request(req.message)
        yield _sse_event("meta", {
            "subject": subject,
            "topic": topic,
            "class_level": class_level,
        })

        # Build prompt
        history = get_session_history(req.thread_id, limit=10)
        log_session(req.thread_id, "user", req.message)
        history_context = (
            "\n".join(
                [f"{m['role']}: {m['content']}" for m in history]
            )
            if history else "No previous context."
        )
        prompt = (
            f"Previous Conversation Context:\n{history_context}"
            f"\n\nTeacher's message:\n{req.message}"
        )

        # Stream from LLM
        accumulator = JSONBlockAccumulator()
        full_text = ""

        async for token in stream_openrouter(
            CLASSGEN_JSON_SYSTEM_PROMPT, prompt
        ):
            full_text += token
            new_blocks = accumulator.feed(token)
            for block in new_blocks:
                yield _sse_event("block", block)

        # Log the full response
        log_session(req.thread_id, "assistant", full_text)

        # Parse the complete response
        lesson_pack, _ = parse_lesson_response(full_text)

        # If no blocks were streamed, try fallback
        if not accumulator.blocks_emitted:
            yield _sse_event("fallback", {"raw_text": full_text})

        # Finalize: PDF + homework code
        reply, pdf_url, homework_code, pack = await _finalize_lesson(
            full_text,
            req.message,
            req.thread_id,
            teacher_phone,
            class_level,
            subject,
            topic,
            lesson_pack=lesson_pack,
        )

        # Track usage
        if teacher_phone and _has_content(reply, pack):
            log_usage(teacher_phone, "lesson")

        # Cache
        if class_level and subject and topic and pack:
            cache_lesson(
                subject, topic, class_level, full_text,
                lesson_json=pack.model_dump(),
            )

        yield _sse_event("done", {
            "pdf_url": pdf_url,
            "homework_code": homework_code,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/config")
async def get_config():
    """Return client-visible feature flag state.

    Returns *effective* state — flags that depend on ``structured_output``
    show ``false`` when their prerequisite is off, preventing the frontend
    from attempting SSE when the server can only return blocking JSON.
    """
    return {
        "sse_streaming": flags.effective_sse_streaming,
        "structured_output": flags.structured_output,
    }
