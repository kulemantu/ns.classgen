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
    get_class_leaderboard, get_student_progress,
    save_parent_subscription, get_covered_topics,
    log_session, set_active_thread,
    get_teacher_lesson_stats,
)
from curriculum import suggest_topics, parse_class_string, list_subjects


@dataclass
class CommandResult:
    reply: str
    session_action: str | None = None  # "reset", "register", etc.
    new_thread_id: str | None = None


def handle_command(body: str, phone: str, base_url: str) -> CommandResult | None:
    """Try to match body against known commands. Returns None if not a command."""
    text = body.strip()
    lower = text.lower()

    # --- Greetings (don't waste LLM tokens) ---
    if lower in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening"):
        return CommandResult(
            reply='Welcome to ClassGen! Send a topic to generate a lesson '
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
        return CommandResult(reply="Send: results CODE\n\nExample: results MATH42\n\nOr send 'my codes' to see your homework codes.")

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

    # Not a command — fall through to LLM
    return None


# --- Command implementations ---

def _cmd_reset(phone: str) -> CommandResult:
    import time
    new_id = f"{phone}_{int(time.time())}"
    set_active_thread(phone, new_id)
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
        "  register [Name] -- create your profile\n"
        "  my page -- view your profile URL\n"
        "  add class: SS2 Biology -- add a class\n\n"
        "*Homework & Results*\n"
        "  my codes -- list your recent codes\n"
        "  results CODE -- quiz results summary\n"
        "  log CODE -- submission order & top scorer\n"
        "  leaderboard CODE -- top students\n"
        "  progress [Name] [Class] -- student history\n\n"
        "*Parents*\n"
        "  subscribe parent [phone] [name] [class]\n\n"
        "*Curriculum*\n"
        "  suggest [class] -- topic suggestions\n"
        "  covered [class] -- what you've taught\n\n"
        "*Other*\n"
        "  stats -- your lesson stats\n"
        "  study [topic] -- quick recap\n"
        "  new -- start a fresh lesson\n"
        "  help -- this menu"
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


# --- V2.1 Commands ---

def _cmd_leaderboard(code: str) -> CommandResult:
    if not code:
        return CommandResult(reply="Send: leaderboard CODE\n\nExample: leaderboard MATH42")
    ranked = get_class_leaderboard(code, limit=10)
    if not ranked:
        return CommandResult(reply=f"No submissions yet for *{code}*.")
    lines = [f"*Leaderboard for {code}*\n"]
    for i, s in enumerate(ranked, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        name = s.get("student_name", "?")
        score = s.get("score", 0)
        total = s.get("total", 5)
        lines.append(f"  {medal} {name} -- {score}/{total}")
    return CommandResult(reply="\n".join(lines))


def _cmd_student_progress(args: str) -> CommandResult:
    """Parse 'progress Amina SS2' -> name='Amina', class='SS2'."""
    parts = args.rsplit(maxsplit=1)
    if len(parts) < 2:
        return CommandResult(reply="Send: progress [Name] [Class]\n\nExample: progress Amina SS2")
    name, student_class = parts[0].strip(), parts[1].strip()
    history = get_student_progress(name, student_class)
    if not history:
        return CommandResult(reply=f"No quiz history found for *{name}* in *{student_class}*.")
    total_quizzes = len(history)
    total_score = sum(s.get("score", 0) for s in history)
    total_possible = sum(s.get("total", 5) for s in history)
    pct = round(total_score / total_possible * 100) if total_possible else 0
    lines = [
        f"*Progress for {name} ({student_class})*\n",
        f"Quizzes taken: {total_quizzes}",
        f"Total score: {total_score}/{total_possible} ({pct}%)\n",
        "*Recent:*",
    ]
    for s in history[:5]:
        code = s.get("homework_code", "?")
        lines.append(f"  {code}: {s.get('score', 0)}/{s.get('total', 5)}")
    return CommandResult(reply="\n".join(lines))


def _cmd_subscribe_parent(teacher_phone: str, args: str) -> CommandResult:
    """Parse 'subscribe parent +234xxx Amina SS2 Biology'."""
    match = re.match(r"(\+?\d{10,15})\s+(.+?)\s+(SS\d|JSS\d)\s*(.*)", args, re.IGNORECASE)
    if not match:
        return CommandResult(
            reply="Send: subscribe parent [phone] [student name] [class]\n\n"
                  "Example: subscribe parent +2348012345678 Amina SS2 Biology"
        )
    parent_phone = match.group(1)
    student_name = match.group(2).strip()
    student_class = (match.group(3) + " " + match.group(4)).strip()

    teacher = get_teacher_by_phone(teacher_phone)
    if not teacher:
        return CommandResult(reply="Register first. Send: register [Your Name]")

    save_parent_subscription(parent_phone, teacher_phone, student_name, student_class)
    return CommandResult(
        reply=f"Parent *{parent_phone}* subscribed for *{student_name}* in *{student_class}*.\n\n"
              f"They'll receive weekly updates via WhatsApp."
    )


def _cmd_study_mode(topic: str) -> CommandResult:
    """Study mode returns None to let the LLM handle it with a study-focused prompt."""
    # We return a special result that main.py can use to trigger a study-mode LLM call
    return CommandResult(
        reply="",
        session_action="study",
        new_thread_id=topic,  # pass the topic through
    )


# --- Stats & Submission Log ---

def _cmd_stats(phone: str, base_url: str) -> CommandResult:
    """Show teacher's lesson generation stats."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return CommandResult(reply="Register first. Send: register [Your Name]")

    stats = get_teacher_lesson_stats(phone)
    slug = teacher.get("slug", "")
    lines = [
        "*Your ClassGen Stats*\n",
        f"Lessons created: *{stats['total']}*",
        f"This week: *{stats['this_week']}*",
        f"This month: *{stats['this_month']}*",
    ]
    if slug:
        lines.append(f"\nProfile: {base_url}/t/{slug}")
        lines.append(f"Export data: {base_url}/t/{slug}/export")
    return CommandResult(reply="\n".join(lines))


def _cmd_submission_log(code: str) -> CommandResult:
    """Show quiz submissions in order — who finished first, top scorer."""
    if not code:
        return CommandResult(reply="Send: log CODE\n\nExample: log MATH42")
    results = get_quiz_results(code)
    if not results:
        return CommandResult(reply=f"No submissions yet for *{code}*.")

    # Sort by created_at ascending (earliest first)
    by_time = sorted(results, key=lambda s: s.get("created_at", ""))
    # Find top scorer
    top = max(results, key=lambda s: s.get("score", 0))

    lines = [f"*Submission log for {code}* ({len(results)} students)\n"]

    # First finisher
    first = by_time[0]
    lines.append(f"First to finish: *{first.get('student_name', '?')}* "
                 f"({first.get('score', 0)}/{first.get('total', 5)})")

    # Top scorer
    lines.append(f"Highest score: *{top.get('student_name', '?')}* "
                 f"({top.get('score', 0)}/{top.get('total', 5)})\n")

    # Full log
    lines.append("_Submission order:_")
    for i, s in enumerate(by_time, 1):
        name = s.get("student_name", "?")
        score = s.get("score", 0)
        total = s.get("total", 5)
        timestamp = s.get("created_at", "")
        # Show just the time portion if available
        time_str = ""
        if timestamp and "T" in timestamp:
            time_str = f" at {timestamp.split('T')[1][:5]}"
        lines.append(f"  {i}. {name} -- {score}/{total}{time_str}")

    return CommandResult(reply="\n".join(lines))


# --- V3.0a Commands ---

def _cmd_suggest(phone: str, class_name: str) -> CommandResult:
    """Suggest topics from curriculum for a class."""
    teacher = get_teacher_by_phone(phone)
    if not teacher:
        return CommandResult(reply="Register first. Send: register [Your Name]")

    # If no class specified, list teacher's classes
    if not class_name:
        classes = teacher.get("classes", [])
        if not classes:
            return CommandResult(reply="Add a class first. Send: add class: SS2 Biology")
        subjects = list_subjects()
        return CommandResult(
            reply="*Which class?*\n\n" +
                  "\n".join(f"  suggest {c}" for c in classes) +
                  f"\n\nAvailable subjects: {', '.join(subjects)}"
        )

    exam_board, subject, class_level = parse_class_string(class_name)
    if not subject:
        return CommandResult(reply="Example: suggest SS2 Biology")

    covered = get_covered_topics(phone, class_name)
    uncovered, done = suggest_topics(exam_board, subject, class_level, covered)

    if not uncovered and not done:
        return CommandResult(
            reply=f"No curriculum data found for {class_name}. "
                  f"Available subjects: {', '.join(list_subjects())}"
        )

    lines = [f"*Topics for {class_level} {subject}*\n"]

    if uncovered:
        lines.append(f"_Not yet covered ({len(uncovered)})_:")
        for i, t in enumerate(uncovered[:8], 1):
            lines.append(f"  {i}. {t}")
        if len(uncovered) > 8:
            lines.append(f"  ... and {len(uncovered) - 8} more")

    if done:
        lines.append(f"\n_Already covered ({len(done)})_:")
        for t in done[:5]:
            lines.append(f"  - {t}")

    lines.append("\nSend any topic to generate a lesson.")
    return CommandResult(reply="\n".join(lines))


def _cmd_covered(phone: str, class_name: str) -> CommandResult:
    """Show topics a teacher has already generated."""
    if not class_name:
        return CommandResult(reply="Example: covered SS2 Biology")
    covered = get_covered_topics(phone, class_name)
    if not covered:
        return CommandResult(reply=f"No lessons generated yet for *{class_name}*.")
    lines = [f"*Topics covered for {class_name}* ({len(covered)}):\n"]
    for t in covered:
        lines.append(f"  - {t}")
    return CommandResult(reply="\n".join(lines))
