from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from utils import call_openrouter, generate_homework_code
from db import (
    log_session, get_session_history,
    save_homework_code, get_homework_code,
    save_quiz_submission, get_quiz_results,
    get_teacher_by_slug, list_homework_codes_for_teacher,
    log_lesson_generated, get_cached_lesson, cache_lesson,
    get_school, get_school_teachers,
    get_active_thread,
)
from commands import handle_command
from billing import check_usage, log_usage
from notifications import save_push_subscription, notify_quiz_submission
from pdf_generator import generate_pdf_from_markdown
import json
import os
import time
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create static dir if not exists
os.makedirs("static", exist_ok=True)


def _cleanup_old_pdfs(max_age_hours: int = 24):
    """Delete generated PDFs older than max_age_hours on startup."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    cutoff = time.time() - (max_age_hours * 3600)
    count = 0
    for f in os.listdir(static_dir):
        if f.startswith("lesson_plan_") and f.endswith(".pdf"):
            path = os.path.join(static_dir, f)
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
                count += 1
    if count:
        print(f"Cleaned up {count} old PDF(s)")


@asynccontextmanager
async def lifespan(app):
    _cleanup_old_pdfs()
    yield


app = FastAPI(title="ClassGen MAP Backend", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Shared system prompt — single source of truth for both endpoints
CLASSGEN_SYSTEM_PROMPT = """You are ClassGen, a lesson pack engine for secondary school teachers in Africa.

You generate structured, ready-to-teach lesson packs. Teachers should be able to read your output and walk into a classroom with zero extra preparation.

## PHASE 1: COLLECT CONTEXT

You need: Subject, Topic, and Class level. If ANY are missing from the conversation, ask for ALL missing fields in a single message. Do NOT ask for them one at a time across multiple turns -- teachers on WhatsApp over 2G cannot afford multiple round-trips.

Default duration to 40 minutes if not specified.

## LANGUAGE
If the teacher writes in French, Yoruba, Hausa, Swahili, or any other language, respond in that language. If they explicitly request a bilingual lesson (e.g. "in English and Yoruba"), generate the lesson with both languages -- English for the main content and the local language for key terms, instructions to students, and the homework narrative.

When asking a clarifying question, end your response with this exact format:
SUGGESTIONS: [Option A] | [Option B] | [Option C]

Example:
What class level are we working with?
SUGGESTIONS: [SS1 / Grade 10] | [SS2 / Grade 11] | [SS3 / Grade 12]

## PHASE 2: GENERATE LESSON PACK

Once you have subject, topic, and class level, output ONLY the structured blocks below. No text outside blocks.

IMPORTANT CONTENT RULES:
- Write for a teacher who will READ THIS ALOUD or paraphrase it in class. Use natural, spoken language.
- Design for classrooms of 30-60 students with exercise books, pens, and a chalkboard. No projectors, no internet, no printouts unless explicitly available.
- The homework MUST be completable in a student's exercise book with only a pen. Students may not have access to technology at home.
- Be specific. "Discuss in groups" is not an activity. "Groups of 4, each group gets a different scenario, 8 minutes to prepare, 1 minute to present" is an activity.
- Be age-appropriate and curriculum-aware for the class level given.
- Detect the exam board from the class level:
  - SS1-SS3 (Senior Secondary, Nigeria/West Africa): WAEC and NECO syllabus. Reference past WAEC/NECO question styles in Teacher Notes.
  - JSS1-JSS3 (Junior Secondary, Nigeria/West Africa): Basic Education Certificate Examination (BECE).
  - Form 1-4 (Kenya/East Africa): KNEC (Kenya National Examinations Council) syllabus. Reference KCSE question styles in Teacher Notes.
  - If the teacher specifies "Cambridge", "IGCSE", or "AS/A-Level", follow the Cambridge International syllabus.
  - If the teacher specifies a specific exam board, use that instead.
  - Always mention the relevant exam board in the TEACHER_NOTES block under EXAM TIP.

[BLOCK_START_OPENER]
Title: [A catchy hook -- not "Introduction to X"]
Summary: [What the teacher does in the first 2 minutes to grab attention]
Details: [A specific script or action. Examples of good openers:
- A "what if" question: "What if I told you the water you drank today is older than the dinosaurs?"
- A visible demo: "Watch what happens when I drop these two objects at the same time."
- A challenge: "I bet nobody in this room can explain why the sky is blue. By the end of this lesson, all of you will."
- A cold-open story: "In 1928, a scientist came back from holiday to find mould on his experiment..."
Write the actual words the teacher would say, not a description of what they should do.]
[BLOCK_END]

[BLOCK_START_EXPLAIN]
Title: [Clear concept title]
Summary: [One sentence: what this concept IS, in plain language]
Details: [Explain the core concept as if speaking to the class. Use simple analogies. Weave in one surprising or mind-blowing fact naturally -- do not separate it out. Include any key formula, definition, or rule the students need to write down. End with a quick check: "Ask the class: [a question that tests if they understood]."]
[BLOCK_END]

[BLOCK_START_ACTIVITY]
Title: [Name of the activity -- make it sound fun]
Summary: [Format + timing, e.g. "Group relay race -- 12 minutes"]
Details: [Write this as step-by-step instructions the teacher follows:
- Setup (1-2 min): How to split students, what to write on the board, any materials needed.
- Activity (8-12 min): Exactly what students do, round by round or step by step.
- Wrap-up (1-2 min): How the teacher debriefs -- who won, what did we learn, common mistakes.
Design for 30-60 students, fixed desks, exercise books + pens only. Good formats: relay races, think-pair-share, group challenges, quick quiz battles, class debates, gallery walks. Always include group size and timing.]
[BLOCK_END]

[BLOCK_START_HOMEWORK]
Title: [A compelling homework title -- not "Homework Questions"]
Summary: [The format: story problem / detective case / design challenge / exercise book game / journal entry]
Details: [The homework must be completable in an exercise book with only a pen. Choose ONE of these formats and write the FULL assignment:

STORY PROBLEM: Student IS a character in a scenario. They must apply the lesson to solve a real problem. Include the setup, the specific tasks (labelled a, b, c), and what to draw/calculate/write.

DETECTIVE CASE: Present 3-4 pieces of evidence. Student uses lesson concepts to write a "detective report" explaining what happened and why.

DESIGN CHALLENGE: Student creates something in their exercise book -- a poster, a diagram, a labelled design, a map. Specify exactly what it must include.

EXERCISE BOOK GAME: A game the student draws in their book and plays with a family member or alone. Include the rules, the game board layout, and how to win. Examples: vocabulary bingo grid, question-path board game, top-trumps cards to draw and compare.

JOURNAL ENTRY: Student writes from the perspective of a scientist, historical figure, or professional. Specify the scenario, what must be included, and minimum length.

End with: "Teacher assessment tip: [how to quickly check 30+ exercise books for this homework -- what to look for in 5 seconds per book]"]
[BLOCK_END]

[BLOCK_START_TEACHER_NOTES]
Title: Teacher Notes
Summary: Quick reference for the teacher
Details: [Include ALL of these:
- EXPECTED ANSWERS: Key answers for the activity and homework.
- COMMON MISTAKES: 2-3 mistakes students typically make on this topic and how to address them.
- QUICK CHECK: "If a student can answer [specific question], they understood today's lesson."
- NEXT LESSON LINK: One sentence on what comes next and how today's lesson connects to it.
- EXAM TIP: If relevant, mention how this topic typically appears in exams (WAEC, NECO, KNEC/KCSE, Cambridge, etc.).]
[BLOCK_END]
"""


def _strip_images_for_pdf(text: str) -> str:
    """Strip markdown images and base64 data URLs to prevent FPDF crashes."""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text, flags=re.DOTALL)
    text = re.sub(r'data:image.*?(?=["\'\)\s])', '', text)
    return text


def _has_lesson_blocks(text: str) -> bool:
    """Check if the response contains structured lesson blocks (not just a clarifying question)."""
    return bool(re.search(r'\[BLOCK_START_', text))


def _clean_block_markers_for_pdf(text: str) -> str:
    """Strip block markers and format for readable PDF output."""
    # Remove block markers
    text = re.sub(r'\[BLOCK_START_\w+\]', '', text)
    text = re.sub(r'\[BLOCK_END\]', '\n', text)
    # Strip image markdown and data URLs
    text = _strip_images_for_pdf(text)
    # Clean up excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_homework_block(text: str) -> str:
    """Extract the HOMEWORK block content from a lesson response."""
    match = re.search(r'\[BLOCK_START_HOMEWORK\](.*?)\[BLOCK_END\]', text, re.DOTALL)
    return match.group(1).strip() if match else ""


QUIZ_GENERATION_PROMPT = """You are a quiz generator. Given lesson content, generate exactly 5 multiple-choice questions.

Return ONLY valid JSON — no markdown, no code fences, no explanation. The response must be a JSON array:
[
  {
    "question": "The question text",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct": 0
  }
]

"correct" is the zero-based index of the correct option (0=A, 1=B, 2=C, 3=D).

Rules:
- Questions should test understanding, not just recall
- All 4 options should be plausible
- Questions should be appropriate for the class level
- Keep language simple and clear"""


async def _generate_quiz_questions(lesson_content: str) -> list:
    """Generate 5 MCQ questions from lesson content via a second LLM call."""
    try:
        raw = await call_openrouter(QUIZ_GENERATION_PROMPT, lesson_content)
        if not raw:
            return []
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r'^```\w*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) > 0:
            return questions[:5]
    except Exception as e:
        print(f"Error generating quiz: {e}")
    return []


def _parse_lesson_request(msg: str) -> tuple[str, str, str]:
    """Best-effort parse of 'SS2 Biology: Photosynthesis' -> (class_level, subject, topic)."""
    # Match patterns like "SS2 Biology: Photosynthesis" or "JSS3 Chemistry Acids"
    m = re.match(r"(SS\d|JSS\d)\s+(\w+)[:\s]+(.+)", msg.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2).strip(), m.group(3).strip()
    return "", "", ""


async def _generate_lesson(user_message: str, thread_id: str, limit: int = 10, teacher_phone: str = "") -> tuple[str, str | None, str | None]:
    """Shared logic: log input, call LLM, generate PDF + homework code, log output.
    Returns (reply, pdf_url, homework_code)."""

    # Check content cache before spending LLM tokens
    class_level, subject, topic = _parse_lesson_request(user_message)
    if class_level and subject and topic:
        cached = get_cached_lesson(subject, topic, class_level)
        if cached:
            print(f"[cache hit] {class_level} {subject}: {topic}")
            log_session(thread_id, "user", user_message)
            log_session(thread_id, "assistant", cached)
            return await _finalize_lesson(cached, user_message, thread_id, teacher_phone, class_level, subject, topic)

    # Fetch history BEFORE logging the new message (avoids duplicate in LLM context)
    history = get_session_history(thread_id, limit=limit)
    log_session(thread_id, "user", user_message)

    history_context = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in history]
    ) if history else "No previous context."

    prompt = f"Previous Conversation Context:\n{history_context}\n\nTeacher's message:\n{user_message}"

    assistant_reply = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, prompt)

    if not assistant_reply:
        return "I'm sorry, my AI engine is currently resting. Please try again soon.", None, None

    log_session(thread_id, "assistant", assistant_reply)

    # Cache if this was a parseable lesson request
    if class_level and subject and topic and _has_lesson_blocks(assistant_reply):
        cache_lesson(subject, topic, class_level, assistant_reply)

    return await _finalize_lesson(assistant_reply, user_message, thread_id, teacher_phone, class_level, subject, topic)


async def _finalize_lesson(assistant_reply: str, user_message: str, thread_id: str,
                           teacher_phone: str, class_level: str, subject: str,
                           topic: str) -> tuple[str, str | None, str | None]:
    """Generate PDF, homework code, log history. Shared by cache-hit and fresh paths."""
    pdf_url = None
    homework_code = None
    if _has_lesson_blocks(assistant_reply):
        try:
            pdf_text = _clean_block_markers_for_pdf(assistant_reply)
            pdf_filename = generate_pdf_from_markdown(pdf_text, subtitle=user_message[:120])
            pdf_url = f"/static/{pdf_filename}" if pdf_filename else None
        except Exception as e:
            print(f"Error generating PDF: {e}")

        try:
            homework_code = generate_homework_code()
            homework_block = _extract_homework_block(assistant_reply)
            quiz_questions = await _generate_quiz_questions(assistant_reply)
            save_homework_code(homework_code, thread_id, assistant_reply, quiz_questions, homework_block, teacher_phone=teacher_phone)
        except Exception as e:
            print(f"Error generating homework code: {e}")
            homework_code = None

        # Log to lesson history for curriculum tracking
        if teacher_phone and class_level and subject and topic:
            log_lesson_generated(teacher_phone, subject, topic, class_level)

    return assistant_reply, pdf_url, homework_code

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>ClassGen Local Backend Proxy is running.</h1><p>index.html not found.</p>")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/vapid-key")
async def vapid_key():
    """Return the VAPID public key for push subscription."""
    from notifications import VAPID_PUBLIC_KEY
    return {"publicKey": VAPID_PUBLIC_KEY}


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict
    teacher_id: str = ""  # thread_id or phone


@app.post("/api/push/subscribe")
async def push_subscribe(sub: PushSubscription):
    """Register a push notification subscription."""
    subscription = {"endpoint": sub.endpoint, "keys": sub.keys}
    teacher_id = sub.teacher_id or sub.endpoint[:40]
    save_push_subscription(teacher_id, subscription)
    return {"ok": True}


def _whatsapp_summary(lesson_text: str, homework_code: str | None, base_url: str) -> str:
    """Create a WhatsApp-friendly summary (under 1500 chars) from a full lesson pack."""
    titles = re.findall(
        r'\[BLOCK_START_(\w+)\].*?Title:\s*\*{0,2}(.*?)\*{0,2}\s*(?:\n|$)',
        lesson_text, re.DOTALL
    )
    labels = {
        "OPENER": "Hook", "EXPLAIN": "Concept", "ACTIVITY": "Activity",
        "HOMEWORK": "Homework", "TEACHER_NOTES": "Notes",
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


@app.post("/webhook/twilio")
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
        twiml_response.message(
            'Welcome to ClassGen! Send a topic to get started '
            '-- e.g. "SS2 Biology: Photosynthesis"\n\n'
            'Send "help" for all commands.'
        )
        return Response(content=str(twiml_response), media_type="application/xml")

    # Try command router first
    cmd_result = handle_command(body, phone, base_url)
    if cmd_result:
        # Study mode: send topic to LLM with a recap prompt
        if cmd_result.session_action == "study":
            topic = cmd_result.new_thread_id or body
            study_prompt = (
                "Give a concise study recap of this topic for a secondary school student. "
                "Include: key definitions, the main formula/rule, one example, and 3 quick "
                "self-test questions. Keep it under 1000 characters. Topic: " + topic
            )
            recap = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, study_prompt)
            twiml_response.message(recap or "Could not generate a recap right now. Try again.")
            return Response(content=str(twiml_response), media_type="application/xml")

        twiml_response.message(cmd_result.reply)
        return Response(content=str(twiml_response), media_type="application/xml")

    # Not a command — generate a lesson
    # Check usage quota first
    usage = check_usage(phone)
    if not usage.allowed:
        twiml_response.message(usage.message)
        return Response(content=str(twiml_response), media_type="application/xml")

    thread_id = get_active_thread(phone)
    ai_response_text, pdf_url, homework_code = await _generate_lesson(body, thread_id, teacher_phone=phone)
    if _has_lesson_blocks(ai_response_text):
        log_usage(phone, "lesson")

    # Build WhatsApp-friendly reply (keep under 1500 chars to avoid truncation)
    if _has_lesson_blocks(ai_response_text) and len(ai_response_text) > 1500:
        reply_text = _whatsapp_summary(ai_response_text, homework_code, base_url)
    else:
        reply_text = ai_response_text
        if homework_code:
            reply_text += f"\n\nHomework Code: {homework_code}\nStudents visit: {base_url}/h/{homework_code}"

    msg = twiml_response.message(reply_text)

    # Attach PDF as media if available
    if from_number and pdf_url:
        full_pdf_url = f"{base_url}{pdf_url}"
        msg.media(full_pdf_url)

    return Response(content=str(twiml_response), media_type="application/xml")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str


@app.post("/api/chat")
async def local_chat_endpoint(req: ChatRequest):
    """Local JSON endpoint for the web UI."""
    # Handle greetings and help on web too (no phone, use thread_id as identity)
    cmd_result = handle_command(req.message, req.thread_id, "")
    if cmd_result and cmd_result.session_action != "study":
        return {"reply": cmd_result.reply, "pdf_url": None, "homework_code": None}

    assistant_reply, pdf_url, homework_code = await _generate_lesson(req.message, req.thread_id)

    return {
        "reply": assistant_reply,
        "pdf_url": pdf_url,
        "homework_code": homework_code,
    }

@app.get("/h/{code}", response_class=HTMLResponse)
async def homework_page(code: str):
    """Serve the lightweight quiz page for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return HTMLResponse("<h1>Homework code not found</h1><p>Check the code and try again.</p>", status_code=404)
    homework_path = os.path.join(os.path.dirname(__file__), "homework.html")
    if not os.path.exists(homework_path):
        return HTMLResponse("<h1>Quiz page not available</h1>", status_code=500)
    return FileResponse(homework_path)


@app.get("/api/h/{code}")
async def homework_data(code: str):
    """Return homework data as JSON for the quiz page to consume."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return {
        "code": hw["code"],
        "homework_block": hw["homework_block"],
        "quiz_questions": hw.get("quiz_questions", []),
    }


class QuizSubmission(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    student_class: str = Field(..., min_length=1, max_length=50)
    answers: list[int]


@app.post("/h/{code}/submit")
async def submit_quiz(request: Request, code: str, submission: QuizSubmission):
    """Grade and store a student's quiz submission."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "Homework code not found"}, status_code=404)

    questions = hw.get("quiz_questions", [])
    if not questions:
        return JSONResponse({"error": "No quiz available for this code"}, status_code=400)

    total = len(questions)
    score = 0
    results = []
    for i, q in enumerate(questions):
        student_answer = submission.answers[i] if i < len(submission.answers) else -1
        correct = q.get("correct", -1)
        is_correct = student_answer == correct
        if is_correct:
            score += 1
        results.append({
            "question": q["question"],
            "options": q["options"],
            "student_answer": student_answer,
            "correct": correct,
            "is_correct": is_correct,
        })

    save_quiz_submission(code.upper(), submission.student_name, submission.student_class, submission.answers, score, total)

    # Notify teacher via push notification
    teacher_id = hw.get("teacher_phone") or hw.get("thread_id", "")
    if teacher_id:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        notify_quiz_submission(teacher_id, code.upper(), submission.student_name, score, total, base_url)

    return {
        "score": score,
        "total": total,
        "results": results,
    }


@app.get("/h/{code}/results", response_class=HTMLResponse)
async def homework_results_page(code: str):
    """Serve the teacher results page for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return HTMLResponse("<h1>Homework code not found</h1><p>Check the code and try again.</p>", status_code=404)
    results_path = os.path.join(os.path.dirname(__file__), "results.html")
    if not os.path.exists(results_path):
        return HTMLResponse("<h1>Results page not available</h1>", status_code=500)
    return FileResponse(results_path)


@app.get("/api/h/{code}/results")
async def homework_results_data(code: str):
    """Return quiz submission results for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "not_found"}, status_code=404)

    submissions = get_quiz_results(code.upper())
    total_submissions = len(submissions)
    avg_score = (
        sum(s.get("score", 0) for s in submissions) / total_submissions
        if total_submissions > 0 else 0
    )

    # Per-question breakdown
    questions = hw.get("quiz_questions", [])
    question_stats = []
    for i, q in enumerate(questions):
        correct_count = sum(
            1 for s in submissions
            if i < len(s.get("answers", [])) and s["answers"][i] == q.get("correct", -1)
        )
        question_stats.append({
            "question": q["question"],
            "correct_count": correct_count,
            "total_attempts": total_submissions,
            "percent_correct": round(correct_count / total_submissions * 100) if total_submissions else 0,
        })

    return {
        "code": code.upper(),
        "total_submissions": total_submissions,
        "average_score": round(avg_score, 1),
        "total_questions": len(questions),
        "submissions": [
            {
                "student_name": s.get("student_name"),
                "student_class": s.get("student_class"),
                "score": s.get("score"),
                "total": s.get("total"),
                "created_at": s.get("created_at"),
            }
            for s in submissions
        ],
        "question_stats": question_stats,
    }


@app.get("/t/{slug}", response_class=HTMLResponse)
async def teacher_profile(request: Request, slug: str):
    """Public teacher profile page."""
    teacher = get_teacher_by_slug(slug)
    if not teacher:
        return HTMLResponse("<h1>Teacher not found</h1>", status_code=404)

    phone = teacher.get("phone", "")
    codes_raw = list_homework_codes_for_teacher(phone, limit=10)
    codes = []
    for hw in codes_raw:
        block = hw.get("homework_block", "")
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", block)
        codes.append({
            "code": hw.get("code", ""),
            "title": title_match.group(1).strip() if title_match else "Homework",
        })

    return templates.TemplateResponse(request, "profile.html", {
        "teacher": teacher,
        "codes": codes,
    })


@app.get("/s/{slug}", response_class=HTMLResponse)
async def school_admin(request: Request, slug: str):
    """School admin dashboard."""
    school = get_school(slug)
    if not school:
        return HTMLResponse("<h1>School not found</h1>", status_code=404)

    teachers = get_school_teachers(slug)
    # Enrich with lesson counts
    for t in teachers:
        codes = list_homework_codes_for_teacher(t.get("phone", ""), limit=100)
        t["lesson_count"] = len(codes)

    total_lessons = sum(t.get("lesson_count", 0) for t in teachers)
    total_students = 0  # Would aggregate quiz submissions across all teachers

    return templates.TemplateResponse(request, "admin.html", {
        "school": school,
        "teachers": teachers,
        "total_lessons": total_lessons,
        "total_students": total_students,
    })


@app.post("/api/dev/seed")
async def dev_seed():
    """Seed mock data for local testing. Only works without Supabase."""
    from db import supabase as _sb, save_teacher
    if _sb:
        return JSONResponse({"error": "Only available in local dev mode"}, status_code=403)

    # Seed a teacher
    teacher = save_teacher("+2348012345678", "Mrs. Okafor", "Lagos Model School")
    from db import add_teacher_class
    add_teacher_class("+2348012345678", "SS2 Biology")
    add_teacher_class("+2348012345678", "SS1 Mathematics")

    # Seed a homework code linked to the teacher
    code = "TEST01"
    quiz = [
        {"question": "What gas do plants absorb during photosynthesis?", "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide", "D) Hydrogen"], "correct": 2},
        {"question": "Where in the leaf does photosynthesis mainly occur?", "options": ["A) Roots", "B) Stem", "C) Chloroplasts", "D) Bark"], "correct": 2},
        {"question": "What is the green pigment in leaves called?", "options": ["A) Melanin", "B) Chlorophyll", "C) Haemoglobin", "D) Keratin"], "correct": 1},
        {"question": "What is the main product of photosynthesis?", "options": ["A) Protein", "B) Starch", "C) Glucose", "D) Fat"], "correct": 2},
        {"question": "Which of these is NOT needed for photosynthesis?", "options": ["A) Sunlight", "B) Water", "C) Soil", "D) Carbon dioxide"], "correct": 2},
    ]
    hw_block = (
        "Title: The Plant Engineer's Report\n"
        "Summary: Story problem\n"
        "Details: You are a botanist hired by a village to explain why their crops are dying."
    )
    save_homework_code(code, "dev_seed", "Mock lesson content", quiz, hw_block, teacher_phone="+2348012345678")
    return {"seeded": code, "teacher_slug": teacher.get("slug"), "quiz_questions": len(quiz)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
