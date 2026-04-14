#!/usr/bin/env python3
"""Mock E2E Parity Runner v1.0.0

Cross-channel parity testing for ClassGen — compares web (/api/chat) and
WhatsApp (/webhook/twilio) responses for the same inputs.

Usage:
    python .mock/e2e/cli.py parity lesson       Lesson generation parity
    python .mock/e2e/cli.py parity commands      Command handling parity
    python .mock/e2e/cli.py parity onboarding    Onboarding flow parity
    python .mock/e2e/cli.py parity all           All parity tests
    python .mock/e2e/cli.py web "message"        Web channel only
    python .mock/e2e/cli.py info                 Show config

OPTIONS
    --url URL               Server URL [default: http://localhost:8000]
    --from PHONE            WhatsApp sender [default: whatsapp:+2348012345678]
    --transcript-dir DIR    Output directory [default: .local/transcripts/]
    --json                  JSON output
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure sibling imports resolve
_pkg_dir = str(Path(__file__).parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
# Also add the twilio-api mock for simulator access
_twilio_dir = str(Path(__file__).parent.parent / "twilio-api")
if _twilio_dir not in sys.path:
    sys.path.insert(0, _twilio_dir)

from parity import ParityResult, compare_responses, print_parity_result  # noqa: E402
from report import generate_html_report  # noqa: E402
from web_client import send_chat  # noqa: E402


def parse_args(argv: list[str]) -> tuple[str, list[str], dict]:
    opts: dict = {
        "url": os.environ.get("TWILIO_MOCK_URL", "http://localhost:8000"),
        "from": "whatsapp:+2348012345678",
        "transcript_dir": ".local/transcripts",
        "json": False,
    }
    positional: list[str] = []
    command = ""
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg == "--url" and i + 1 < len(argv):
            opts["url"] = argv[i + 1]
            i += 2
        elif arg == "--from" and i + 1 < len(argv):
            opts["from"] = argv[i + 1]
            i += 2
        elif arg == "--transcript-dir" and i + 1 < len(argv):
            opts["transcript_dir"] = argv[i + 1]
            i += 2
        elif arg == "--json":
            opts["json"] = True
            i += 1
        elif arg in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        elif not command and not arg.startswith("-"):
            command = arg
            i += 1
        elif not arg.startswith("-"):
            positional.append(arg)
            i += 1
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)

    return command, positional, opts


# ---------------------------------------------------------------------------
# Parity test runners
# ---------------------------------------------------------------------------


def _run_command_parity(command: str, opts: dict) -> ParityResult:
    """Run a single command through web and WhatsApp, compare."""
    from simulator import build_payload, send  # type: ignore[import]

    # Web
    web_result = send_chat(opts["url"], command)

    # WhatsApp
    wa_payload = build_payload(
        "text_message",
        from_number=opts["from"],
        to_number="whatsapp:+14155238886",
        profile_name="Parity Test",
        body=command,
    )
    wa_result = send(opts["url"], wa_payload, no_signature=True)

    # Normalize for comparison
    web_data = {
        "status": web_result.status,
        "reply": web_result.reply,
        "pdf_url": web_result.pdf_url,
        "homework_code": web_result.homework_code,
        "blocks": web_result.blocks,
        "duration_ms": web_result.duration_ms,
    }

    wa_messages = wa_result.messages
    wa_text = " ".join(m["body"] for m in wa_messages) if wa_messages else ""
    has_pdf = any(bool(m.get("media")) for m in wa_messages)

    wa_data = {
        "status": wa_result.status,
        "messages": wa_messages,
        "response_text": wa_text,
        "has_pdf_media": has_pdf,
        "homework_code": "",  # Not directly extractable from TwiML summary
        "block_count": 0,
        "duration_ms": wa_result.duration_ms,
    }

    return compare_responses(
        f"command_{command}", web_data, wa_data, ["response_ok", "has_content"]
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_parity(positional: list[str], opts: dict) -> None:
    suite = positional[0] if positional else "all"

    commands_to_test = {
        "commands": ["help", "hello"],
        "onboarding": ["hello"],
        "lesson": ["SS2 Biology: Photosynthesis, 40 mins"],
    }

    if suite == "all":
        suites = ["commands", "onboarding"]
    elif suite in commands_to_test:
        suites = [suite]
    else:
        print(f"Unknown suite: {suite}", file=sys.stderr)
        print("Available: commands, onboarding, lesson, all", file=sys.stderr)
        sys.exit(1)

    results: list[ParityResult] = []
    for s in suites:
        cmds = commands_to_test.get(s, [])
        for cmd in cmds:
            result = _run_command_parity(cmd, opts)
            results.append(result)
            if not opts["json"]:
                print_parity_result(result)

    # Save reports
    out_dir = Path(opts["transcript_dir"])
    for result in results:
        result.save(out_dir)
        html_path = generate_html_report(result, out_dir)
        if not opts["json"]:
            print(f"  Report: {html_path}")

    if opts["json"]:
        all_ok = all(r.all_passed for r in results)
        data = [json.loads(r.to_json()) for r in results]
        print(json.dumps({"ok": all_ok, "data": data}))
        sys.exit(0 if all_ok else 1)

    all_ok = all(r.all_passed for r in results)
    sys.exit(0 if all_ok else 1)


def cmd_web(positional: list[str], opts: dict) -> None:
    if not positional:
        print('Usage: web "message"', file=sys.stderr)
        sys.exit(1)
    message = positional[0]
    result = send_chat(opts["url"], message)

    if opts["json"]:
        print(json.dumps({"ok": result.ok, "data": result.raw}))
        sys.exit(0 if result.ok else 1)

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    RESET = "\033[0m"

    if result.ok:
        print(f"\n{GREEN}  Web ({result.duration_ms}ms):{RESET}")
        print(f"  {result.reply[:500]}")
        if result.pdf_url:
            print(f"  {CYAN}PDF:{RESET} {result.pdf_url}")
        if result.homework_code:
            print(f"  {CYAN}Code:{RESET} {result.homework_code}")
        print()
    else:
        print(f"\n{RED}  HTTP {result.status}: {result.error[:300]}{RESET}\n")


def cmd_info(positional: list[str], opts: dict) -> None:
    info = {
        "url": opts["url"],
        "web_endpoint": opts["url"].rstrip("/") + "/api/chat",
        "whatsapp_endpoint": opts["url"].rstrip("/") + "/webhook/twilio",
        "from": opts["from"],
        "transcript_dir": opts["transcript_dir"],
    }

    if opts["json"]:
        print(json.dumps({"ok": True, "data": info}))
        sys.exit(0)

    CYAN = "\033[0;36m"
    RESET = "\033[0m"
    print(f"\n  {CYAN}E2E Parity Runner{RESET}\n")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print()


COMMANDS = {
    "parity": cmd_parity,
    "web": cmd_web,
    "info": cmd_info,
}


def main():
    command, positional, opts = parse_args(sys.argv[1:])

    if not command:
        print(__doc__)
        sys.exit(0)

    if command not in COMMANDS:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[command](positional, opts)


if __name__ == "__main__":
    main()
