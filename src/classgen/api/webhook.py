"""Twilio WhatsApp webhook router -- POST /webhook/twilio."""

from __future__ import annotations

import os
import re

from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from classgen.api.chat import _generate_lesson, _has_lesson_blocks
from classgen.channels.whatsapp import WhatsAppAdapter
from classgen.commands.router import handle_command
from classgen.content.onboarding import whatsapp_welcome
from classgen.content.prompts import CLASSGEN_SYSTEM_PROMPT
from classgen.core.feature_flags import flags
from classgen.data import get_active_thread, get_teacher_by_phone, save_teacher
from classgen.data.subscriptions import log_usage
from classgen.data.teachers import is_onboarded, mark_onboarded
from classgen.services.billing_service import check_usage
from classgen.services.llm import call_openrouter

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _whatsapp_summary(lesson_text: str, homework_code: str | None, base_url: str) -> str:
    """Create a WhatsApp-friendly summary (under 1500 chars) from a full lesson pack."""
    titles = re.findall(
        r"\[BLOCK_START_(\w+)\].*?Title:\s*\*{0,2}(.*?)\*{0,2}\s*(?:\n|$)",
        lesson_text,
        re.DOTALL,
    )
    labels = {
        "OPENER": "Hook",
        "EXPLAIN": "Concept",
        "ACTIVITY": "Activity",
        "HOMEWORK": "Homework",
        "TEACHER_NOTES": "Notes",
    }

    parts = ["*ClassGen Lesson Pack*\n"]
    for block_type, title in titles:
        label = labels.get(block_type, block_type.title())
        parts.append(f"  *{label}:* {title.strip()}")

    if homework_code:
        parts.append(f"\n*Homework Code:* {homework_code}")
        parts.append(f"Students visit: {base_url}/h/{homework_code}")

    parts.append("\nFull lesson plan attached as PDF.")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/webhook/twilio")
async def twilio_webhook(request: Request):
    """Endpoint for receiving WhatsApp messages from Twilio."""
    form_data = await request.form()

    # Validate Twilio signature if auth token is configured
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if auth_token:
        validator = RequestValidator(auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        if not validator.validate(url, dict(form_data), signature):
            return Response(content="Forbidden", status_code=403)

    from_number = form_data.get("From", "")
    body = str(form_data.get("Body", ""))
    media_url = str(form_data.get("MediaUrl0", ""))
    content_type = str(form_data.get("MediaContentType0", ""))

    print(f"Received from {from_number}: {body} (Media: {media_url})")

    twiml_response = MessagingResponse()
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    phone = str(from_number)

    # Reject voice notes gracefully
    if media_url and "audio" in content_type:
        twiml_response.message(
            "Voice notes aren't supported yet. Please type your request "
            '-- e.g. "SS2 Biology: Photosynthesis"'
        )
        return Response(content=str(twiml_response), media_type="application/xml")

    if not body.strip():
        twiml_response.message(whatsapp_welcome(base_url))
        return Response(content=str(twiml_response), media_type="application/xml")

    # Onboarding: check if user has accepted terms
    if not is_onboarded(phone):
        upper = body.strip().upper()
        if upper == "YES":
            # Create minimal teacher record if needed, then mark onboarded
            if not get_teacher_by_phone(phone):
                save_teacher(phone, phone, phone)
            mark_onboarded(phone)
            twiml_response.message(
                "You're all set! Send a topic to generate your first "
                'lesson -- e.g. "SS2 Biology: Photosynthesis"\n\n'
                'Send "help" for all commands.'
            )
            return Response(content=str(twiml_response), media_type="application/xml")
        if upper == "HELP":
            pass  # Fall through to command router
        else:
            twiml_response.message(whatsapp_welcome(base_url))
            return Response(content=str(twiml_response), media_type="application/xml")

    # Try command router first
    cmd_result = handle_command(body, phone, base_url)
    if cmd_result:
        # Study mode: send topic to LLM with a recap prompt
        if cmd_result.session_action == "study":
            topic = cmd_result.new_thread_id or body
            study_prompt = (
                "Give a concise study recap of this topic"
                " for a secondary school student. "
                "Include: key definitions, the main "
                "formula/rule, one example, and 3 quick "
                "self-test questions. Keep it under "
                "1000 characters. Topic: " + topic
            )
            recap = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, study_prompt)
            twiml_response.message(recap or "Could not generate a recap right now. Try again.")
            return Response(content=str(twiml_response), media_type="application/xml")

        twiml_response.message(cmd_result.reply)
        return Response(content=str(twiml_response), media_type="application/xml")

    # Not a command -- generate a lesson
    # Check usage quota first
    usage = check_usage(phone)
    if not usage.allowed:
        twiml_response.message(usage.message)
        return Response(content=str(twiml_response), media_type="application/xml")

    thread_id = get_active_thread(phone)
    ai_response_text, pdf_url, homework_code, lesson_pack = await _generate_lesson(
        body, thread_id, teacher_phone=phone
    )
    has_content = _has_lesson_blocks(ai_response_text) or (
        lesson_pack is not None and len(lesson_pack.blocks) > 0
    )
    if has_content:
        log_usage(phone, "lesson")

    # Store lesson flow for WhatsApp navigation (sections, next, prev, etc.)
    if lesson_pack and has_content:
        from classgen.data.wa_flows import WAFlow, set_flow

        set_flow(
            phone,
            WAFlow(
                type="lesson_browse",
                step="menu",
                data={
                    "lesson_pack": lesson_pack.model_dump(),
                    "homework_code": homework_code,
                    "pdf_url": f"{base_url}{pdf_url}" if pdf_url else None,
                    "current_block": 0,
                },
            ),
        )

    # Build WhatsApp-friendly reply (keep under 1500 chars to avoid truncation)
    if has_content and (len(ai_response_text) > 1500 or lesson_pack):
        if lesson_pack and flags.structured_output:
            wa_adapter = WhatsAppAdapter()
            reply_text = wa_adapter.render_lesson(
                lesson_pack, homework_code=homework_code, base_url=base_url
            )
        else:
            reply_text = _whatsapp_summary(ai_response_text, homework_code, base_url)
        # Add navigation hint when a lesson flow was stored
        if lesson_pack:
            reply_text += "\n\nReply 'sections' to browse the full lesson."
    else:
        reply_text = ai_response_text
        if homework_code:
            reply_text += (
                f"\n\nHomework Code: {homework_code}\nStudents visit: {base_url}/h/{homework_code}"
            )

    msg = twiml_response.message(reply_text)

    # Attach PDF as media if available
    if from_number and pdf_url:
        full_pdf_url = f"{base_url}{pdf_url}"
        msg.media(full_pdf_url)

    return Response(content=str(twiml_response), media_type="application/xml")
