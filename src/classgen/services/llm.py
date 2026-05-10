"""OpenRouter LLM client and utility functions."""

from __future__ import annotations

import asyncio
import os
import random
import string
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)

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

# Default model for all three call sites. Override with CLASSGEN_LLM_MODEL for
# A/B benchmarks; production leaves this unset to use grok-4.1-fast.
_DEFAULT_MODEL = os.environ.get("CLASSGEN_LLM_MODEL", "x-ai/grok-4.1-fast")


class LLMUnavailableError(Exception):
    """Raised when an LLM call exhausted retries and produced no content.

    Endpoints translate this into channel-appropriate UX (502 + retry envelope
    for web, friendly TwiML for WhatsApp). Internal sentinel — never surfaced
    in raw form to users.
    """


# Transient errors are worth one retry. Auth (401), bad-request (400), and
# not-found (404) are not — retrying them just doubles the latency on a
# permanent failure.
_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)
_RETRY_BACKOFF_S = 0.8


def _log_llm_error(label: str, exc: Exception, attempt: int) -> None:
    """Structured-ish stdout log for LLM failures (greppable in docker logs)."""
    status = getattr(exc, "status_code", None)
    print(
        f"[llm.error] label={label} attempt={attempt} "
        f"class={type(exc).__name__} status={status} msg={exc}",
        flush=True,
    )


async def _create_chat_completion(
    system_prompt: str, user_message: str, model: str, **kwargs
) -> str | None:
    completion = await openrouter_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        **kwargs,
    )
    return completion.choices[0].message.content


async def _call_with_retry(
    label: str, system_prompt: str, user_message: str, model: str, **kwargs
) -> str | None:
    """Single retry on transient errors; bail immediately on permanent ones."""
    try:
        return await _create_chat_completion(system_prompt, user_message, model, **kwargs)
    except _RETRYABLE_EXCEPTIONS as exc:
        _log_llm_error(label, exc, attempt=1)
        await asyncio.sleep(_RETRY_BACKOFF_S)
        try:
            return await _create_chat_completion(system_prompt, user_message, model, **kwargs)
        except Exception as retry_exc:
            _log_llm_error(label, retry_exc, attempt=2)
            return None
    except Exception as exc:
        _log_llm_error(label, exc, attempt=1)
        return None


async def call_openrouter(
    system_prompt: str, user_message: str, model: str = _DEFAULT_MODEL
) -> str | None:
    """Call the LLM via OpenRouter (blocking, returns full response)."""
    return await _call_with_retry("text", system_prompt, user_message, model)


async def call_openrouter_json(
    system_prompt: str, user_message: str, model: str = _DEFAULT_MODEL
) -> str | None:
    """Call the LLM requesting JSON output.

    When ``FF_JSON_RESPONSE_FORMAT`` is enabled, passes
    ``response_format={"type": "json_object"}`` to the API. Falls back
    to a plain call if the model doesn't support it.
    """
    if not flags.json_response_format:
        return await _call_with_retry("json", system_prompt, user_message, model)

    # Try with response_format first; if the model rejects it, fall back to
    # the plain text path (which itself has retry).
    try:
        return await _create_chat_completion(
            system_prompt, user_message, model, response_format={"type": "json_object"}
        )
    except Exception as exc:
        if "response_format" in str(exc).lower():
            print(f"response_format not supported, retrying without: {exc}", flush=True)
            return await call_openrouter(system_prompt, user_message, model)
        if isinstance(exc, _RETRYABLE_EXCEPTIONS):
            _log_llm_error("json", exc, attempt=1)
            await asyncio.sleep(_RETRY_BACKOFF_S)
            try:
                return await _create_chat_completion(
                    system_prompt, user_message, model,
                    response_format={"type": "json_object"},
                )
            except Exception as retry_exc:
                _log_llm_error("json", retry_exc, attempt=2)
                return None
        _log_llm_error("json", exc, attempt=1)
        return None


async def stream_openrouter(
    system_prompt: str, user_message: str, model: str = _DEFAULT_MODEL
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
