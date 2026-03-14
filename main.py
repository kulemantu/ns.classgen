from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse
from utils import (
    call_openrouter, log_session, get_session_history,
    generate_homework_code, save_homework_code, get_homework_code,
    save_quiz_submission, get_quiz_results,
)
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

app = FastAPI(title="ClassGen MAP Backend")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared system prompt — single source of truth for both endpoints
CLASSGEN_SYSTEM_PROMPT = """You are ClassGen, a lesson pack engine for secondary school teachers in Africa.

You generate structured, ready-to-teach lesson packs. Teachers should be able to read your output and walk into a classroom with zero extra preparation.

## PHASE 1: COLLECT CONTEXT

You need: Subject, Topic, and Class level. If any are missing from the conversation, ask ONE short clarifying question. Do not ask multiple questions at once.

Default duration to 40 minutes if not specified.

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
  - SS1-SS3 (Senior Secondary): WAEC and NECO syllabus. Reference past WAEC/NECO question styles in Teacher Notes.
  - JSS1-JSS3 (Junior Secondary): Basic Education Certificate Examination (BECE).
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
- EXAM TIP: If relevant, mention how this topic typically appears in exams (WAEC, NECO, Cambridge, etc.).]
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
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error generating quiz: {e}")
    return []


async def _generate_lesson(user_message: str, thread_id: str, limit: int = 3) -> tuple[str, str | None, str | None]:
    """Shared logic: log input, call LLM, generate PDF + homework code, log output.
    Returns (reply, pdf_url, homework_code)."""
    log_session(thread_id, "user", user_message)

    history = get_session_history(thread_id, limit=limit)
    history_context = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in history]
    ) if history else "No previous context."

    prompt = f"Previous Conversation Context:\n{history_context}\n\nTeacher's message:\n{user_message}"

    assistant_reply = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, prompt)

    if not assistant_reply:
        return "I'm sorry, my AI engine is currently resting. Please try again soon.", None, None

    log_session(thread_id, "assistant", assistant_reply)

    # Only generate PDF + homework code for actual lesson packs, not clarifying questions
    pdf_url = None
    homework_code = None
    if _has_lesson_blocks(assistant_reply):
        try:
            pdf_text = _clean_block_markers_for_pdf(assistant_reply)
            pdf_filename = generate_pdf_from_markdown(pdf_text)
            pdf_url = f"/static/{pdf_filename}" if pdf_filename else None
        except Exception as e:
            print(f"Error generating PDF: {e}")

        # Generate homework code + quiz questions
        try:
            homework_code = generate_homework_code()
            homework_block = _extract_homework_block(assistant_reply)
            quiz_questions = await _generate_quiz_questions(assistant_reply)
            save_homework_code(homework_code, thread_id, assistant_reply, quiz_questions, homework_block)
        except Exception as e:
            print(f"Error generating homework code: {e}")
            homework_code = None

    return assistant_reply, pdf_url, homework_code

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>ClassGen Local Backend Proxy is running.</h1><p>index.html not found.</p>")
@app.post("/webhook/twilio")
async def twilio_webhook(request: Request):
    """Endpoint for receiving WhatsApp messages from Twilio."""
    form_data = await request.form()

    from_number = form_data.get("From", "")
    body = form_data.get("Body", "")
    media_url = form_data.get("MediaUrl0", "")
    content_type = form_data.get("MediaContentType0", "")

    print(f"Received from {from_number}: {body} (Media: {media_url})")

    twiml_response = MessagingResponse()

    # Thread tracking — phone number + hourly window
    session_window = str(int(time.time() // 3600))
    thread_id = f"{from_number}_{session_window}"

    # Voice note handling (transcription placeholder)
    user_input = body
    if media_url and "audio" in content_type:
        # TODO: Transcription via Whisper
        user_input = f"[Voice Note Transcription Placeholder: Teacher asked for a lesson plan. Original body: {body}]"

    if not user_input.strip() and not media_url:
        twiml_response.message("Welcome to ClassGen! Send a topic or voice note to get started.")
        return Response(content=str(twiml_response), media_type="application/xml")

    ai_response_text, pdf_url, homework_code = await _generate_lesson(user_input, thread_id)

    reply_text = ai_response_text
    if homework_code:
        reply_text += f"\n\nHomework Code: {homework_code}\nStudents visit: /h/{homework_code}"

    msg = twiml_response.message(reply_text)

    # Attach PDF as media if available
    if from_number and pdf_url:
        full_pdf_url = f"{request.url.scheme}://{request.url.netloc}{pdf_url}"
        msg.media(full_pdf_url)

    return Response(content=str(twiml_response), media_type="application/xml")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str


@app.post("/api/chat")
async def local_chat_endpoint(request: ChatRequest):
    """Local JSON endpoint for the web UI. Bypasses Twilio."""
    assistant_reply, pdf_url, homework_code = await _generate_lesson(request.message, request.thread_id)

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
async def submit_quiz(code: str, submission: QuizSubmission):
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

    return {
        "score": score,
        "total": total,
        "results": results,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
