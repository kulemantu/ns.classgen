"""Web channel HTTP client for /api/chat."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field


@dataclass
class WebResult:
    status: int
    reply: str = ""
    pdf_url: str | None = None
    homework_code: str | None = None
    blocks: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    raw: dict = field(default_factory=dict)
    ok: bool = True
    error: str = ""


def send_chat(
    url: str,
    message: str,
    thread_id: str | None = None,
    *,
    timeout: int = 45,
) -> WebResult:
    """POST to /api/chat, return parsed response."""
    import time as _time

    chat_url = url.rstrip("/")
    if not chat_url.endswith("/api/chat"):
        chat_url += "/api/chat"

    if not thread_id:
        thread_id = f"parity_{uuid.uuid4().hex[:8]}"

    payload = json.dumps({"message": message, "thread_id": thread_id}).encode("utf-8")
    req = urllib.request.Request(
        chat_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = _time.monotonic()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8")
        elapsed = int((_time.monotonic() - t0) * 1000)
        data = json.loads(body)

        # Extract lesson_pack blocks if available
        blocks = []
        lesson_pack = data.get("lesson_pack")
        if lesson_pack and isinstance(lesson_pack, dict):
            blocks = lesson_pack.get("blocks", [])

        return WebResult(
            status=resp.status,
            reply=data.get("reply", ""),
            pdf_url=data.get("pdf_url"),
            homework_code=data.get("homework_code"),
            blocks=blocks,
            duration_ms=elapsed,
            raw=data,
        )

    except urllib.error.HTTPError as e:
        elapsed = int((_time.monotonic() - t0) * 1000)
        body = e.read().decode("utf-8") if e.fp else ""
        return WebResult(
            status=e.code,
            duration_ms=elapsed,
            ok=False,
            error=body[:500],
        )

    except urllib.error.URLError as e:
        elapsed = int((_time.monotonic() - t0) * 1000)
        return WebResult(
            status=0,
            duration_ms=elapsed,
            ok=False,
            error=str(e.reason),
        )
