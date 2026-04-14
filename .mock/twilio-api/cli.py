#!/usr/bin/env python3
"""Mock Twilio WhatsApp Simulator v1.0.0

Send production-realistic Twilio payloads to a running ClassGen instance.
Computes valid X-Twilio-Signature headers, parses TwiML responses,
and supports one-shot commands and interactive conversation mode.

Usage:
    python .mock/twilio-api/cli.py <command> [args] [options]

COMMANDS
  send TEXT               Send a text message (default)
  send:voice              Send a voice note
  send:image [URL]        Send an image attachment
  send:button TEXT        Send a button/quick reply
  send:forward TEXT       Send a forwarded message
  send:empty              Send empty body
  scenario NAME           Run a named scenario
  scenario:list           List available scenarios
  payload NAME            Send a raw payload fixture
  payload:list            List available fixtures
  callback STATUS         Send a status callback (delivered/read/failed)
  chat                    Interactive conversation mode
  info                    Show config and connectivity

OPTIONS
  --url URL               Webhook URL [default: http://localhost:8000]
  --from PHONE            Sender [default: whatsapp:+2348012345678]
  --to PHONE              Receiver [default: whatsapp:+14155238886]
  --token TOKEN           Auth token [env: TWILIO_MOCK_AUTH_TOKEN]
  --no-signature          Skip X-Twilio-Signature header
  --profile NAME          WhatsApp profile name [default: Mrs. Okafor]
  --json                  JSON output: {"ok": bool, "data": ...}
  --verbose               Show full HTTP request/response
  --delay SECONDS         Delay between scenario steps [default: 1.0]
  --transcript            Save JSON + HTML transcript of the run
  --transcript-dir DIR    Transcript output dir [default: .local/transcripts/]

EXAMPLES
  python .mock/twilio-api/cli.py send "hello"
  python .mock/twilio-api/cli.py send "SS2 Biology: Photosynthesis"
  python .mock/twilio-api/cli.py send:voice
  python .mock/twilio-api/cli.py scenario onboarding
  python .mock/twilio-api/cli.py callback delivered
  python .mock/twilio-api/cli.py chat --from whatsapp:+254712345678
  python .mock/twilio-api/cli.py info --json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure sibling imports resolve when invoked directly
_pkg_dir = str(Path(__file__).parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from simulator import (  # noqa: E402, I001
    DEFAULT_FROM,
    DEFAULT_MEDIA_URL,
    DEFAULT_PROFILE,
    DEFAULT_TOKEN,
    DEFAULT_TO,
    Colors,
    SimResult,
    build_payload,
    list_fixtures,
    list_scenarios,
    run_scenario,
    send,
)
from twiml_parser import format_messages  # noqa: E402


# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> tuple[str, list[str], dict]:
    """Parse CLI args into (command, positional_args, options).

    Returns command name, positional args, and a dict of options.
    """
    opts: dict = {
        "url": os.environ.get("TWILIO_MOCK_URL", "http://localhost:8000"),
        "from": DEFAULT_FROM,
        "to": DEFAULT_TO,
        "token": os.environ.get("TWILIO_MOCK_AUTH_TOKEN", DEFAULT_TOKEN),
        "no_signature": False,
        "profile": DEFAULT_PROFILE,
        "json": False,
        "verbose": False,
        "delay": 1.0,
        "transcript": False,
        "transcript_dir": ".local/transcripts",
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
        elif arg == "--to" and i + 1 < len(argv):
            opts["to"] = argv[i + 1]
            i += 2
        elif arg == "--token" and i + 1 < len(argv):
            opts["token"] = argv[i + 1]
            i += 2
        elif arg == "--profile" and i + 1 < len(argv):
            opts["profile"] = argv[i + 1]
            i += 2
        elif arg == "--delay" and i + 1 < len(argv):
            opts["delay"] = float(argv[i + 1])
            i += 2
        elif arg == "--no-signature":
            opts["no_signature"] = True
            i += 1
        elif arg == "--json":
            opts["json"] = True
            i += 1
        elif arg == "--verbose":
            opts["verbose"] = True
            i += 1
        elif arg == "--transcript":
            opts["transcript"] = True
            i += 1
        elif arg == "--transcript-dir" and i + 1 < len(argv):
            opts["transcript_dir"] = argv[i + 1]
            opts["transcript"] = True
            i += 2
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
# Output helpers
# ---------------------------------------------------------------------------


def _json_out(ok: bool, data) -> None:
    print(json.dumps({"ok": ok, "data": data}))
    sys.exit(0 if ok else 1)


def _print_result(result: SimResult, opts: dict) -> None:
    """Print a SimResult to the terminal."""
    if opts["json"]:
        _json_out(
            result.ok,
            {
                "status": result.status,
                "messages": result.messages,
                "raw": result.body[:2000] if not result.ok else None,
            },
        )
        return

    if result.ok and result.messages:
        print(f"\n{Colors.GREEN}  ClassGen:{Colors.RESET}")
        print(format_messages(result.messages))
        print()
    elif result.ok:
        print(f"\n{Colors.GREEN}  {result.status} OK{Colors.RESET}")
        if result.body:
            print(f"  {result.body[:500]}\n")
    else:
        print(f"\n{Colors.RED}  HTTP {result.status}{Colors.RESET}")
        print(f"  {result.body[:500]}\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_send(positional: list[str], opts: dict) -> None:
    body = positional[0] if positional else "hello"
    payload = build_payload(
        "text_message",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
        body=body,
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_send_voice(positional: list[str], opts: dict) -> None:
    payload = build_payload(
        "voice_note",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_send_image(positional: list[str], opts: dict) -> None:
    media_url = positional[0] if positional else DEFAULT_MEDIA_URL
    body = positional[1] if len(positional) > 1 else ""
    payload = build_payload(
        "image_attachment",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
        body=body,
        media_url=media_url,
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_send_button(positional: list[str], opts: dict) -> None:
    body = positional[0] if positional else "YES"
    payload = build_payload(
        "button_reply",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
        body=body,
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_send_forward(positional: list[str], opts: dict) -> None:
    body = positional[0] if positional else "Forwarded message"
    payload = build_payload(
        "forwarded_message",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
        body=body,
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_send_empty(positional: list[str], opts: dict) -> None:
    payload = build_payload(
        "empty_body",
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_callback(positional: list[str], opts: dict) -> None:
    status = positional[0] if positional else "delivered"
    fixture_map = {
        "delivered": "status_delivered",
        "read": "status_read",
        "failed": "status_failed",
    }
    fixture = fixture_map.get(status)
    if not fixture:
        print(f"Unknown status: {status}. Choose from: {', '.join(fixture_map)}", file=sys.stderr)
        sys.exit(1)
    payload = build_payload(
        fixture,
        from_number=opts["from"],
        to_number=opts["to"],
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_payload(positional: list[str], opts: dict) -> None:
    if not positional:
        print("Usage: payload NAME", file=sys.stderr)
        sys.exit(1)
    name = positional[0]
    payload = build_payload(
        name,
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
    )
    result = send(
        opts["url"],
        payload,
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
    )
    _print_result(result, opts)


def cmd_payload_list(positional: list[str], opts: dict) -> None:
    fixtures = list_fixtures()
    if opts["json"]:
        _json_out(True, fixtures)
    for f in fixtures:
        print(f"  {f}")


def cmd_scenario(positional: list[str], opts: dict) -> None:
    if not positional:
        print("Usage: scenario NAME", file=sys.stderr)
        print("Use 'scenario:list' to see available scenarios.", file=sys.stderr)
        sys.exit(1)
    name = positional[0]
    result = run_scenario(
        name,
        url=opts["url"],
        from_number=opts["from"],
        to_number=opts["to"],
        profile_name=opts["profile"],
        token=opts["token"],
        no_signature=opts["no_signature"],
        verbose=opts["verbose"],
        transcript=opts["transcript"],
        transcript_dir=opts["transcript_dir"],
        delay=opts["delay"],
        json_output=opts["json"],
    )
    if opts["json"]:
        _json_out(result["ok"], result)
    sys.exit(0 if result["ok"] else 1)


def cmd_scenario_list(positional: list[str], opts: dict) -> None:
    scenarios = list_scenarios()
    if opts["json"]:
        _json_out(True, scenarios)
    for s in scenarios:
        print(f"  {s['name']:20s} {s['description']}")


def cmd_info(positional: list[str], opts: dict) -> None:
    info = {
        "url": opts["url"],
        "webhook": opts["url"].rstrip("/") + "/webhook/twilio",
        "from": opts["from"],
        "to": opts["to"],
        "profile": opts["profile"],
        "token_set": bool(opts["token"]),
        "no_signature": opts["no_signature"],
        "fixtures": list_fixtures(),
        "scenarios": list_scenarios(),
    }

    if opts["json"]:
        _json_out(True, info)

    print(f"\n  {Colors.CYAN}Mock Twilio WhatsApp Simulator{Colors.RESET}\n")
    print(f"  Webhook URL:  {info['webhook']}")
    print(f"  From:         {info['from']}")
    print(f"  To:           {info['to']}")
    print(f"  Profile:      {info['profile']}")
    print(f"  Token:        {'set' if info['token_set'] else 'not set'}")
    print(f"  Signature:    {'disabled' if info['no_signature'] else 'enabled'}")
    print(f"\n  Fixtures:     {', '.join(info['fixtures'])}")
    print(f"  Scenarios:    {', '.join(s['name'] for s in info['scenarios'])}")
    print()


def cmd_chat(positional: list[str], opts: dict) -> None:
    """Interactive conversation mode."""
    print(f"\n{Colors.CYAN}  Mock Twilio WhatsApp Chat{Colors.RESET}")
    print(f"  Sending to: {opts['url']}")
    print("  Type a message or use /commands. /quit to exit.\n")
    print("  Slash commands: /voice /image /forward /button /empty")
    print("  /status STATUS  /from PHONE  /profile NAME  /scenario NAME  /raw  /quit\n")

    show_raw = False

    while True:
        try:
            prompt = f"[{opts['profile']} {opts['from'].replace('whatsapp:', '')}] > "
            text = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!")
            break

        if not text:
            continue

        if text == "/quit":
            print("  Bye!")
            break

        if text == "/raw":
            show_raw = not show_raw
            print(f"  Raw XML display: {'on' if show_raw else 'off'}")
            continue

        if text.startswith("/from "):
            opts["from"] = text[6:].strip()
            print(f"  From set to: {opts['from']}")
            continue

        if text.startswith("/profile "):
            opts["profile"] = text[9:].strip()
            print(f"  Profile set to: {opts['profile']}")
            continue

        if text.startswith("/scenario "):
            name = text[10:].strip()
            run_scenario(
                name,
                url=opts["url"],
                from_number=opts["from"],
                to_number=opts["to"],
                profile_name=opts["profile"],
                token=opts["token"],
                no_signature=opts["no_signature"],
                verbose=opts["verbose"],
                delay=opts["delay"],
            )
            continue

        if text.startswith("/status "):
            status = text[8:].strip()
            cmd_callback([status], opts)
            continue

        # Map slash commands to fixtures
        fixture_map = {
            "/voice": "voice_note",
            "/image": "image_attachment",
            "/forward": "forwarded_message",
            "/button": "button_reply",
            "/empty": "empty_body",
        }

        if text in fixture_map:
            fixture = fixture_map[text]
            payload = build_payload(
                fixture,
                from_number=opts["from"],
                to_number=opts["to"],
                profile_name=opts["profile"],
            )
        else:
            # Regular text message
            payload = build_payload(
                "text_message",
                from_number=opts["from"],
                to_number=opts["to"],
                profile_name=opts["profile"],
                body=text,
            )

        result = send(
            opts["url"],
            payload,
            token=opts["token"],
            no_signature=opts["no_signature"],
            verbose=opts["verbose"],
        )

        if show_raw and result.body:
            print(f"\n{Colors.DIM}{result.body}{Colors.RESET}")

        if result.ok and result.messages:
            print(f"\n{Colors.GREEN}  ClassGen:{Colors.RESET}")
            print(format_messages(result.messages))
            print()
        elif not result.ok:
            print(f"\n{Colors.RED}  HTTP {result.status}: {result.body[:300]}{Colors.RESET}\n")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

COMMANDS = {
    "send": cmd_send,
    "send:voice": cmd_send_voice,
    "send:image": cmd_send_image,
    "send:button": cmd_send_button,
    "send:forward": cmd_send_forward,
    "send:empty": cmd_send_empty,
    "scenario": cmd_scenario,
    "scenario:list": cmd_scenario_list,
    "payload": cmd_payload,
    "payload:list": cmd_payload_list,
    "callback": cmd_callback,
    "chat": cmd_chat,
    "info": cmd_info,
}


def main():
    command, positional, opts = parse_args(sys.argv[1:])

    if not command:
        # Default: if positional args given, treat as "send"
        if positional:
            command = "send"
        else:
            print(__doc__)
            sys.exit(0)

    if command not in COMMANDS:
        # Maybe it's a bare text to send
        if not command.startswith("-"):
            positional.insert(0, command)
            command = "send"
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print("Run with --help to see available commands.", file=sys.stderr)
            sys.exit(1)

    COMMANDS[command](positional, opts)


if __name__ == "__main__":
    main()
