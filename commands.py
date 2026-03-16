"""WhatsApp command router for ClassGen.

Parses incoming text against registered commands before falling through
to the LLM lesson generator. Each handler returns a CommandResult or None
(None means "not a command, pass to LLM").
"""

import re
from dataclasses import dataclass
from db import (
    save_teacher, get_teacher_by_phone, add_teacher_class,
    list_homework_codes_for_teacher, get_quiz_results,
    log_session,
)


@dataclass
class CommandResult:
    reply: str
    session_action: str | None = None  # "reset", "register", etc.
    new_thread_id: str | None = None


def handle_command(body: str, phone: str, base_url: str) -> CommandResult | None:
    """Try to match body against known commands. Returns None if not a command."""
    text = body.strip()
    lower = text.lower()

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
    if lower.startswith("results ") or lower.startswith("my results "):
        code = re.sub(r"^(my )?results\s+", "", text, flags=re.IGNORECASE).strip().upper()
        return _cmd_results(phone, code, base_url)

    if lower in ("my codes", "my homework", "codes"):
        return _cmd_my_codes(phone, base_url)

    # Not a command — fall through to LLM
    return None


# --- Command implementations ---

def _cmd_reset(phone: str) -> CommandResult:
    import time
    new_id = f"{phone}_{int(time.time())}"
    log_session(new_id, "system", "Session reset by teacher.")
    return CommandResult(
        reply="Starting fresh! What subject and topic would you like a lesson on?",
        session_action="reset",
        new_thread_id=new_id,
    )


def _cmd_help(base_url: str) -> CommandResult:
    return CommandResult(reply=(
        "*ClassGen Commands*\n\n"
        "Send any topic to generate a lesson:\n"
        '  _"SS2 Biology: Photosynthesis"_\n\n'
        "*Profile*\n"
        '  register [Your Name] -- create your teacher profile\n'
        "  my page -- view your profile URL\n"
        "  add class: SS2 Biology -- add a class\n\n"
        "*Homework*\n"
        "  my codes -- list your recent homework codes\n"
        "  results CODE -- view quiz results\n\n"
        "*Other*\n"
        "  new -- start a fresh lesson\n"
        "  help -- show this menu"
    ))


def _cmd_register_prompt(phone: str) -> CommandResult:
    teacher = get_teacher_by_phone(phone)
    if teacher:
        return CommandResult(
            reply=f"You're already registered as *{teacher['name']}*. "
                  f"Send a topic to generate a lesson, or send 'help' for commands."
        )
    return CommandResult(
        reply='To register, send: register [Your Name]\n\nExample: register Mrs. Okafor'
    )


def _cmd_register(phone: str, name: str, base_url: str) -> CommandResult:
    if len(name) < 2:
        return CommandResult(reply="Please include your name. Example: register Mrs. Okafor")
    teacher = save_teacher(phone, name)
    slug = teacher.get("slug", "")
    return CommandResult(
        reply=(
            f"Welcome to ClassGen, *{name}*!\n\n"
            f"Your profile page: {base_url}/t/{slug}\n\n"
            f"Now send a topic to generate your first lesson -- e.g. "
            f'"SS2 Biology: Photosynthesis"'
        ),
        session_action="register",
    )


def _cmd_my_page(phone: str, base_url: str) -> CommandResult:
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return CommandResult(
            reply="You haven't registered yet. Send: register [Your Name]"
        )
    slug = teacher.get("slug", "")
    return CommandResult(
        reply=f"Your profile: {base_url}/t/{slug}\n\nClasses: {', '.join(teacher.get('classes', [])) or 'none yet'}\n\nSend 'add class: SS2 Biology' to add classes."
    )


def _cmd_add_class(phone: str, class_name: str) -> CommandResult:
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return CommandResult(reply="Register first. Send: register [Your Name]")
    if not class_name:
        return CommandResult(reply="Example: add class: SS2 Biology")
    add_teacher_class(phone, class_name)
    teacher = get_teacher_by_phone(phone)
    classes = teacher.get("classes", []) if teacher else []
    return CommandResult(
        reply=f"Added *{class_name}*.\n\nYour classes: {', '.join(classes)}"
    )


def _cmd_results(phone: str, code: str, base_url: str) -> CommandResult:
    if not code:
        return CommandResult(reply="Send: results CODE\n\nExample: results MATH42")
    results = get_quiz_results(code)
    if not results:
        return CommandResult(reply=f"No submissions yet for *{code}*.\n\nView online: {base_url}/h/{code}/results")
    total = len(results)
    avg = sum(r.get("score", 0) for r in results) / total
    return CommandResult(
        reply=(
            f"*Results for {code}*\n\n"
            f"Students: {total}\n"
            f"Average: {avg:.1f}/{results[0].get('total', 5)}\n\n"
            f"Full details: {base_url}/h/{code}/results"
        )
    )


def _cmd_my_codes(phone: str, base_url: str) -> CommandResult:
    codes = list_homework_codes_for_teacher(phone, limit=5)
    if not codes:
        return CommandResult(
            reply="No homework codes yet. Generate a lesson to create one!"
        )
    lines = ["*Your recent homework codes:*\n"]
    for hw in codes:
        code = hw.get("code", "?")
        lines.append(f"  *{code}* -- {base_url}/h/{code}")
    return CommandResult(reply="\n".join(lines))
