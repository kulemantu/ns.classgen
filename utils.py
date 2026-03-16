"""OpenRouter LLM client and utility functions."""

import os
import random
import string
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenRouter Client (using standard OpenAI SDK)
_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
if not _openrouter_key:
    print("WARNING: OPENROUTER_API_KEY not set. LLM calls will fail.")

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_openrouter_key or "not-configured",
)


async def call_openrouter(system_prompt: str, user_message: str, model="x-ai/grok-4.1-fast"):
    """Call the LLM via OpenRouter."""
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


def generate_homework_code() -> str:
    """Generate a 6-character homework code like MATH42."""
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join(random.choices(string.digits, k=2))
    return letters + digits
