import os
import random
import string
from openai import AsyncOpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


# Initialize OpenRouter Client (using standard OpenAI SDK)
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "dummy_key"),
)

# Initialize Supabase Client
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase: Client | None = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

async def call_openrouter(system_prompt: str, user_message: str, model="x-ai/grok-4.1-fast"):
    """
    Call the LLM via OpenRouter.
    We default to x-ai/grok-4.1-fast as requested by the user for fast/well-priced responses.
    """
    try:
        completion = await openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return None


def log_session(thread_id: str, role: str, content: str):
    """
    Log interaction to Supabase table `sessions`.
    Requires a table with columns: id, thread_id, role, content, created_at.
    """
    if not supabase:
        print(f"Supabase not configured. Logging locally: [{thread_id}] {role}: {content[:50]}...")
        return
    
    try:
        response = supabase.table("sessions").insert(
            {"thread_id": thread_id, "role": role, "content": content}
        ).execute()
        return response.data
    except Exception as e:
        print(f"Error logging to Supabase: {e}")

def get_session_history(thread_id: str, limit: int = 5):
    """
    Retrieve the last 'limit' messages for a specific thread_id.
    """
    if not supabase:
        return []

    try:
        response = supabase.table("sessions").select("*").eq("thread_id", thread_id).order("created_at", desc=True).limit(limit).execute()
        messages = response.data
        return list(reversed(messages)) # Return chronological order
    except Exception as e:
        print(f"Error retrieving from Supabase: {e}")
        return []


def generate_homework_code() -> str:
    """Generate a 6-character homework code like MATH42."""
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join(random.choices(string.digits, k=2))
    return letters + digits


def save_homework_code(code: str, thread_id: str, lesson_content: str, quiz_questions: list, homework_block: str) -> bool:
    """Save a homework code entry to Supabase."""
    if not supabase:
        print(f"Supabase not configured. Homework code {code} not saved.")
        return False
    try:
        supabase.table("homework_codes").insert({
            "code": code,
            "thread_id": thread_id,
            "lesson_content": lesson_content,
            "quiz_questions": quiz_questions,
            "homework_block": homework_block,
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving homework code: {e}")
        return False


def get_homework_code(code: str) -> dict | None:
    """Retrieve a homework code entry."""
    if not supabase:
        return None
    try:
        response = supabase.table("homework_codes").select("*").eq("code", code).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error retrieving homework code: {e}")
        return None


def save_quiz_submission(homework_code: str, student_name: str, student_class: str, answers: list, score: int, total: int) -> bool:
    """Save a student's quiz submission."""
    if not supabase:
        print(f"Supabase not configured. Submission not saved.")
        return False
    try:
        supabase.table("quiz_submissions").insert({
            "homework_code": homework_code,
            "student_name": student_name,
            "student_class": student_class,
            "answers": answers,
            "score": score,
            "total": total,
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving quiz submission: {e}")
        return False


def get_quiz_results(homework_code: str) -> list:
    """Retrieve all quiz submissions for a homework code."""
    if not supabase:
        return []
    try:
        response = supabase.table("quiz_submissions").select("*").eq("homework_code", homework_code).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error retrieving quiz results: {e}")
        return []
