"""Simple env-var-driven feature flags for ClassGen.

All flags default to False (off). Enable by setting the corresponding
environment variable to "1", "true", or "yes".

Flag hierarchy
--------------
``structured_output`` is the foundation flag. Three other flags extend it:

- ``sse_streaming`` — requires ``structured_output`` (the SSE accumulator
  parses JSON token-by-token, incompatible with legacy block markers).
- ``json_response_format`` — only effective when ``structured_output`` is
  on (the ``response_format`` kwarg is only passed to ``call_openrouter_json``
  and ``stream_openrouter``, both of which are gated on ``structured_output``).
- ``embedded_quiz`` — requires ``structured_output`` (the quiz is only
  present in the JSON lesson pack produced by the JSON system prompt).

Use the ``effective_*`` properties when you need the resolved state that
accounts for dependencies (e.g. for client-facing config).
"""

from __future__ import annotations

import os


class FeatureFlags:
    """Class-based feature flags read from environment variables."""

    @staticmethod
    def _is_enabled(name: str) -> bool:
        return os.environ.get(name, "").lower() in ("1", "true", "yes")

    # --- Raw flags (exactly what the env var says) ---

    @property
    def structured_output(self) -> bool:
        """LLM returns JSON instead of block markers."""
        return self._is_enabled("FF_STRUCTURED_OUTPUT")

    @property
    def sse_streaming(self) -> bool:
        """Web chat uses SSE streaming instead of blocking JSON response."""
        return self._is_enabled("FF_SSE_STREAMING")

    @property
    def json_response_format(self) -> bool:
        """Pass response_format=json_object to the OpenRouter API call."""
        return self._is_enabled("FF_JSON_RESPONSE_FORMAT")

    @property
    def embedded_quiz(self) -> bool:
        """Quiz questions embedded in lesson JSON (skip second LLM call)."""
        return self._is_enabled("FF_EMBEDDED_QUIZ")

    # --- Effective flags (resolve dependencies) ---

    @property
    def effective_sse_streaming(self) -> bool:
        """SSE streaming only works with structured output."""
        return self.sse_streaming and self.structured_output

    @property
    def effective_embedded_quiz(self) -> bool:
        """Embedded quiz only works with structured output."""
        return self.embedded_quiz and self.structured_output

    @property
    def effective_json_response_format(self) -> bool:
        """response_format only reaches the API with structured output."""
        return self.json_response_format and self.structured_output


flags = FeatureFlags()
