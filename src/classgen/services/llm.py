"""OpenRouter LLM client and utility functions."""

from __future__ import annotations

import os
import random
import string
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from classgen.core.feature_flags import flags

load_dotenv()

# Initialize OpenRouter Client (using standard OpenAI SDK)
_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
if not _openrouter_key:
    print("WARNING: OPENROUTER_API_KEY not set. LLM calls will fail.")

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_openrouter_key or "not-configured",
)


async def call_openrouter(
    system_prompt: str, user_message: str, model: str = "x-ai/grok-4.1-fast"
) -> str | None:
    """Call the LLM via OpenRouter (blocking, returns full response)."""
    try:
        completion = await openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return None


async def call_openrouter_json(
    system_prompt: str, user_message: str, model: str = "x-ai/grok-4.1-fast"
) -> str | None:
    """Call the LLM requesting JSON output.

    When ``FF_JSON_RESPONSE_FORMAT`` is enabled, passes
    ``response_format={"type": "json_object"}`` to the API. Falls back
    to a plain call if the model doesn't support it.
    """
    kwargs: dict = {}
    if flags.json_response_format:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        completion = await openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            **kwargs,
        )
        return completion.choices[0].message.content
    except Exception as e:
        if flags.json_response_format and "response_format" in str(e).lower():
            # Model doesn't support response_format — retry without it
            print(f"response_format not supported, retrying without: {e}")
            return await call_openrouter(system_prompt, user_message, model)
        print(f"Error calling OpenRouter (JSON): {e}")
        return None


async def stream_openrouter(
    system_prompt: str, user_message: str, model: str = "x-ai/grok-4.1-fast"
) -> AsyncGenerator[str, None]:
    """Yield tokens from a streaming LLM response."""
    kwargs: dict = {}
    if flags.json_response_format:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        completion = await openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=True,
            **kwargs,
        )
        async for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        if flags.json_response_format and "response_format" in str(e).lower():
            # Model doesn't support response_format — retry without it
            print(f"response_format not supported for streaming, retrying: {e}")
            try:
                completion = await openrouter_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    stream=True,
                )
                async for chunk in completion:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            except Exception as retry_err:
                print(f"Error streaming OpenRouter (retry): {retry_err}")
        else:
            print(f"Error streaming OpenRouter: {e}")


def generate_homework_code() -> str:
    """Generate a 6-character homework code like MATH42."""
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join(random.choices(string.digits, k=2))
    return letters + digits
