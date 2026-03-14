from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse
from utils import call_openrouter, log_session, get_session_history
from pdf_generator import generate_pdf_from_markdown
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


async def _generate_lesson(user_message: str, thread_id: str, limit: int = 3) -> tuple[str, str | None]:
    """Shared logic: log input, call LLM, generate PDF, log output. Returns (reply, pdf_url)."""
    log_session(thread_id, "user", user_message)

    history = get_session_history(thread_id, limit=limit)
    history_context = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in history]
    ) if history else "No previous context."

    prompt = f"Previous Conversation Context:\n{history_context}\n\nTeacher's message:\n{user_message}"

    assistant_reply = await call_openrouter(CLASSGEN_SYSTEM_PROMPT, prompt)

    if not assistant_reply:
        return "I'm sorry, my AI engine is currently resting. Please try again soon.", None

    log_session(thread_id, "assistant", assistant_reply)

    # Only generate PDF for actual lesson packs, not clarifying questions
    pdf_url = None
    if _has_lesson_blocks(assistant_reply):
        try:
            pdf_text = _clean_block_markers_for_pdf(assistant_reply)
            pdf_filename = generate_pdf_from_markdown(pdf_text)
            pdf_url = f"/static/{pdf_filename}" if pdf_filename else None
        except Exception as e:
            print(f"Error generating PDF: {e}")

    return assistant_reply, pdf_url

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

    ai_response_text, pdf_url = await _generate_lesson(user_input, thread_id)

    msg = twiml_response.message(ai_response_text)

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
    assistant_reply, pdf_url = await _generate_lesson(request.message, request.thread_id)

    return {
        "reply": assistant_reply,
        "pdf_url": pdf_url
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
