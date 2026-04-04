"""Web chat API router -- POST /api/chat and lesson generation helpers."""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, Request

from classgen.api.schemas import ChatRequest
from classgen.commands.router import handle_command
from classgen.content.pdf_generator import generate_pdf_from_markdown
from classgen.content.prompts import (
    CLASSGEN_SYSTEM_PROMPT,
    QUIZ_GENERATION_PROMPT,
)
from classgen.data import (
    cache_lesson,
    get_cached_lesson,
    get_session_history,
    get_teacher_by_phone,
    log_lesson_generated,
    log_session,
    save_homework_code,
)
from classgen.data.subscriptions import log_usage
from classgen.services.billing_service import check_usage
from classgen.services.llm import call_openrouter, generate_homework_code

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
) -> tuple[str, str | None, str | None]:
    """Shared logic: log input, call LLM, generate PDF + homework code, log output.

    Returns (reply, pdf_url, homework_code).
    """
    # Check content cache before spending LLM tokens
    class_level, subject, topic = _parse_lesson_request(user_message)
    if class_level and subject and topic:
        cached = get_cached_lesson(subject, topic, class_level)
        if cached:
            print(f"[cache hit] {class_level} {subject}: {topic}")
            log_session(thread_id, "user", user_message)
            log_session(thread_id, "assistant", cached)
            return await _finalize_lesson(
                cached,
                user_message,
                thread_id,
                teacher_phone,
                class_level,
                subject,
                topic,
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

    assistant_reply = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, prompt)

    if not assistant_reply:
        return (
            "I'm sorry, my AI engine is currently resting. Please try again soon.",
            None,
            None,
        )

    log_session(thread_id, "assistant", assistant_reply)

    # Cache if this was a parseable lesson request
    if class_level and subject and topic and _has_lesson_blocks(assistant_reply):
        cache_lesson(subject, topic, class_level, assistant_reply)

    return await _finalize_lesson(
        assistant_reply,
        user_message,
        thread_id,
        teacher_phone,
        class_level,
        subject,
        topic,
    )


async def _finalize_lesson(
    assistant_reply: str,
    user_message: str,
    thread_id: str,
    teacher_phone: str,
    class_level: str,
    subject: str,
    topic: str,
) -> tuple[str, str | None, str | None]:
    """Generate PDF, homework code, log history. Shared by cache-hit and fresh paths."""
    pdf_url = None
    homework_code = None
    if _has_lesson_blocks(assistant_reply):
        try:
            pdf_text = _clean_block_markers_for_pdf(assistant_reply)
            pdf_filename = generate_pdf_from_markdown(
                pdf_text, subtitle=user_message[:120]
            )
            pdf_url = f"/static/{pdf_filename}" if pdf_filename else None
        except Exception as e:
            print(f"Error generating PDF: {e}")

        try:
            homework_code = generate_homework_code()
            homework_block = _extract_homework_block(assistant_reply)
            quiz_questions = await _generate_quiz_questions(assistant_reply)
            save_homework_code(
                homework_code,
                thread_id,
                assistant_reply,
                quiz_questions,
                homework_block,
                teacher_phone=teacher_phone,
            )
        except Exception as e:
            print(f"Error generating homework code: {e}")
            homework_code = None

        # Log to lesson history for curriculum tracking
        if teacher_phone and class_level and subject and topic:
            log_lesson_generated(teacher_phone, subject, topic, class_level)

    return assistant_reply, pdf_url, homework_code


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

    assistant_reply, pdf_url, homework_code = await _generate_lesson(
        req.message, req.thread_id, teacher_phone=teacher_phone
    )

    # Track usage for registered teachers
    if teacher_phone and _has_lesson_blocks(assistant_reply):
        log_usage(teacher_phone, "lesson")

    return {
        "reply": assistant_reply,
        "pdf_url": pdf_url,
        "homework_code": homework_code,
    }
