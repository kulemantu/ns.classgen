"""Transcript recorder and HTML chat view generator.

Records every turn of a WhatsApp mock session and produces:
- JSON transcript (machine-readable, for parity comparison)
- HTML chat view (human-readable, WhatsApp-style bubbles)
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Turn:
    step: int
    description: str
    timestamp: str = ""
    duration_ms: int = 0
    request: dict = field(default_factory=dict)
    response: dict = field(default_factory=dict)
    assertions: dict = field(default_factory=dict)


@dataclass
class Transcript:
    id: str = ""
    timestamp: str = ""
    scenario: str = ""
    channel: str = "whatsapp"
    server_url: str = ""
    config: dict = field(default_factory=dict)
    turns: list[Turn] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.id:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            self.id = f"{ts}_{self.scenario}_{self.channel}"

    def to_json(self) -> str:
        """Compact JSON representation."""
        return json.dumps(asdict(self), separators=(",", ":"))

    def to_html(self) -> str:
        """Self-contained HTML chat view."""
        return _render_html(self)

    def save(self, directory: Path) -> tuple[Path, Path]:
        """Save JSON and HTML transcripts. Returns (json_path, html_path)."""
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"{self.id}.json"
        html_path = directory / f"{self.id}.html"
        json_path.write_text(self.to_json())
        html_path.write_text(self.to_html())
        return json_path, html_path


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #e5ddd5; padding: 20px; }
.container { max-width: 640px; margin: 0 auto; }
.header { background: #075e54; color: #fff; padding: 16px 20px;
          border-radius: 8px 8px 0 0; }
.header h1 { font-size: 18px; font-weight: 600; }
.header .meta { font-size: 12px; opacity: 0.8; margin-top: 4px; }
.chat { background: #e5ddd5; padding: 12px 16px; }
.turn-label { text-align: center; margin: 16px 0 8px;
              font-size: 11px; color: #666; }
.turn-label .badge { display: inline-block; padding: 2px 10px;
                     background: #d1f4cc; border-radius: 10px; }
.turn-label .fail { background: #ffcdd2; }
.bubble { max-width: 85%; padding: 8px 12px; margin: 4px 0;
          border-radius: 8px; font-size: 14px; line-height: 1.5;
          word-wrap: break-word; white-space: pre-wrap; position: relative; }
.bubble .time { font-size: 10px; color: #999; float: right;
                margin-left: 12px; margin-top: 4px; }
.user { background: #dcf8c6; margin-left: auto; border-radius: 8px 0 8px 8px; }
.bot { background: #fff; margin-right: auto; border-radius: 0 8px 8px 8px; }
details { margin-top: 6px; font-size: 12px; }
details summary { cursor: pointer; color: #075e54; }
details pre { background: #f5f5f5; padding: 8px; border-radius: 4px;
              overflow-x: auto; font-size: 11px; margin-top: 4px;
              white-space: pre-wrap; word-break: break-all; }
.summary { background: #fff; padding: 16px 20px; border-radius: 0 0 8px 8px;
           border-top: 1px solid #ddd; }
.summary .stats { display: flex; gap: 20px; margin-top: 8px; }
.summary .stat { font-size: 14px; }
.stat .n { font-weight: 700; font-size: 18px; }
.pass { color: #2e7d32; }
.fail-text { color: #c62828; }
"""


def _render_html(t: Transcript) -> str:
    passed = sum(1 for turn in t.turns if turn.assertions.get("passed", True))
    failed = len(t.turns) - passed
    total_ms = sum(turn.duration_ms for turn in t.turns)

    turns_html = []
    for turn in t.turns:
        step_passed = turn.assertions.get("passed", True)
        badge_cls = "" if step_passed else " fail"
        status = "PASS" if step_passed else "FAIL"

        # Turn divider
        turns_html.append(
            f'<div class="turn-label">'
            f'<span class="badge{badge_cls}">{status} &middot; '
            f"Step {turn.step}: {html.escape(turn.description)}</span></div>"
        )

        # User bubble
        body = turn.request.get("Body", turn.request.get("payload_summary", ""))
        fixture = turn.request.get("fixture", "")
        user_label = html.escape(str(body)) if body else f"[{fixture}]"
        turns_html.append(
            f'<div class="bubble user">{user_label}'
            f'<span class="time">{turn.duration_ms}ms</span></div>'
        )

        # Bot bubble(s)
        messages = turn.response.get("parsed_messages", [])
        if messages:
            for msg in messages:
                msg_body = html.escape(msg.get("body", ""))
                turns_html.append(f'<div class="bubble bot">{msg_body}</div>')
        elif not step_passed:
            status_code = turn.response.get("status", "?")
            raw = html.escape(turn.response.get("raw_body", "")[:300])
            turns_html.append(f'<div class="bubble bot fail-text">HTTP {status_code}: {raw}</div>')

        # Expandable details
        payload_json = json.dumps(turn.request, indent=2, default=str)
        raw_xml = turn.response.get("raw_body", "")
        turns_html.append(
            "<details><summary>Request payload</summary>"
            f"<pre>{html.escape(payload_json)}</pre></details>"
        )
        if raw_xml:
            turns_html.append(
                "<details><summary>Raw TwiML response</summary>"
                f"<pre>{html.escape(raw_xml)}</pre></details>"
            )

    config_line = (
        f"From: {t.config.get('from', '?')} &middot; "
        f"Profile: {t.config.get('profile', '?')} &middot; "
        f"Token: {'set' if t.config.get('token_set') else 'not set'}"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Transcript: {html.escape(t.scenario)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>Transcript: {html.escape(t.scenario)}</h1>
  <div class="meta">{html.escape(t.server_url)} &middot; {html.escape(t.timestamp)}</div>
  <div class="meta">{config_line}</div>
</div>
<div class="chat">
{"".join(turns_html)}
</div>
<div class="summary">
  <strong>Summary</strong>
  <div class="stats">
    <div class="stat"><span class="n pass">{passed}</span> passed</div>
    <div class="stat"><span class="n fail-text">{failed}</span> failed</div>
    <div class="stat"><span class="n">{total_ms}</span>ms total</div>
  </div>
</div>
</div>
</body>
</html>"""
