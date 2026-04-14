"""WhatsApp command router for ClassGen.

Parses incoming text against registered commands before falling through
to the LLM lesson generator. Each handler returns a CommandResult or None
(None means "not a command, pass to LLM").
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CommandResult:
    reply: str
    session_action: str | None = None  # "reset", "register", etc.
    new_thread_id: str | None = None


def handle_command(body: str, phone: str, base_url: str) -> CommandResult | None:
    """Try to match body against known commands. Returns None if not a command."""
    # Lazy import to break circular dependency (handlers imports CommandResult
    # from this module, and we import handler functions from handlers).
    from classgen.commands.handlers import (
        _cmd_add_class,
        _cmd_covered,
        _cmd_help,
        _cmd_leaderboard,
        _cmd_my_codes,
        _cmd_my_page,
        _cmd_register,
        _cmd_register_prompt,
        _cmd_reset,
        _cmd_results,
        _cmd_stats,
        _cmd_student_progress,
        _cmd_study_mode,
        _cmd_submission_log,
        _cmd_subscribe_parent,
        _cmd_suggest,
    )

    text = body.strip()
    lower = text.lower()

    # --- Greetings (don't waste LLM tokens) ---
    if lower in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening"):
        return CommandResult(
            reply="Welcome to ClassGen! Send a topic to generate a lesson "
            '-- e.g. "SS2 Biology: Photosynthesis"\n\n'
            'Send "help" for all commands.'
        )

    # --- Session commands ---
    if lower in ("new", "reset", "new lesson", "start over"):
        return _cmd_reset(phone)

    if lower in ("help", "commands", "menu"):
        return _cmd_help(base_url)

    # --- Teacher profile commands ---
    if lower in ("register", "sign up", "signup"):
        return _cmd_register_prompt(phone)

    if lower.startswith("register ") or lower.startswith("i am "):
        name = re.sub(r"^(register|i am)\s+", "", text, flags=re.IGNORECASE).strip()
        return _cmd_register(phone, name, base_url)

    if lower in ("my page", "my profile", "profile"):
        return _cmd_my_page(phone, base_url)

    if lower.startswith("add class:") or lower.startswith("add class "):
        class_name = re.sub(r"^add class[:\s]+", "", text, flags=re.IGNORECASE).strip()
        return _cmd_add_class(phone, class_name)

    # --- Results commands ---
    if lower in ("results", "my results"):
        return CommandResult(
            reply="Send: results CODE\n\nExample: results MATH42\n\n"
            "Or send 'my codes' to see your homework codes."
        )

    if lower.startswith("results ") or lower.startswith("my results "):
        code = re.sub(r"^(my )?results\s+", "", text, flags=re.IGNORECASE).strip().upper()
        return _cmd_results(phone, code, base_url)

    if lower in ("my codes", "my homework", "codes"):
        return _cmd_my_codes(phone, base_url)

    # --- V2.1: Leaderboard, progress, parent, study ---
    if lower in ("leaderboard", "top"):
        return CommandResult(reply="Send: leaderboard CODE\n\nExample: leaderboard MATH42")

    if lower.startswith("leaderboard ") or lower.startswith("top "):
        code = re.sub(r"^(leaderboard|top)\s+", "", text, flags=re.IGNORECASE).strip().upper()
        return _cmd_leaderboard(code)

    if lower.startswith("progress "):
        # "progress Amina SS2" -> student name + class
        parts = re.sub(r"^progress\s+", "", text, flags=re.IGNORECASE).strip()
        return _cmd_student_progress(parts)

    if lower.startswith("subscribe parent"):
        # "subscribe parent +234... Amina SS2 Biology"
        args = re.sub(r"^subscribe parent\s*", "", text, flags=re.IGNORECASE).strip()
        return _cmd_subscribe_parent(phone, args)

    if lower in ("stats", "my stats", "statistics"):
        return _cmd_stats(phone, base_url)

    if lower.startswith("log "):
        code = re.sub(r"^log\s+", "", text, flags=re.IGNORECASE).strip().upper()
        return _cmd_submission_log(code)

    if lower.startswith("confirm "):
        ref = re.sub(r"^confirm\s+", "", text, flags=re.IGNORECASE).strip()
        return CommandResult(
            reply=f"Payment reference *{ref}* noted. "
            "Our team will verify and activate your subscription within 24 hours."
        )

    if lower.startswith("study "):
        topic = re.sub(r"^study\s+", "", text, flags=re.IGNORECASE).strip()
        return _cmd_study_mode(topic)

    # --- V3.0a: Curriculum assist ---
    if lower.startswith("suggest ") or lower == "suggest":
        class_name = re.sub(r"^suggest\s*", "", text, flags=re.IGNORECASE).strip()
        return _cmd_suggest(phone, class_name)

    if lower.startswith("covered "):
        class_name = re.sub(r"^covered\s+", "", text, flags=re.IGNORECASE).strip()
        return _cmd_covered(phone, class_name)

    # --- Active flow handling (lesson browse, etc.) ---
    from classgen.data.wa_flows import get_flow

    flow = get_flow(phone)
    if flow:
        flow_result = _dispatch_flow(flow, lower, phone)
        if flow_result is not None:
            return flow_result

    # Not a command — fall through to LLM
    return None


def _dispatch_flow(flow, lower: str, phone: str) -> CommandResult | None:
    """Route input to the appropriate flow handler based on flow type."""
    from classgen.commands.handlers import _handle_lesson_flow

    if flow.type == "lesson_browse":
        return _handle_lesson_flow(flow, lower, phone)
    # Future: register, homework_browse, etc.
    return None
