import os
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
