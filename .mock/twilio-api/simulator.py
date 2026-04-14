"""Core engine — build payloads, compute signatures, send HTTP, parse responses."""

from __future__ import annotations  # noqa: I001

import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from twilio.request_validator import RequestValidator
from twiml_parser import format_messages, parse_twiml

PAYLOADS_DIR = Path(__file__).parent / "payloads"
SCENARIOS_DIR = Path(__file__).parent / "scenarios"

DEFAULT_FROM = "whatsapp:+2348012345678"
DEFAULT_TO = "whatsapp:+14155238886"
DEFAULT_PROFILE = "Mrs. Okafor"
DEFAULT_TOKEN = "test_auth_token_for_mock_simulator"
DEFAULT_MEDIA_URL = (
    "https://api.twilio.com/2010-04-01/Accounts/AC00000000000000000000000000000000"
    "/Messages/MM00000000000000000000000000000000/Media/ME00000000000000000000000000000000"
)


@dataclass
class SimResult:
    status: int
    body: str
    messages: list[dict] = field(default_factory=list)
    ok: bool = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def list_fixtures() -> list[str]:
    """List available payload fixture names (without .json extension)."""
    return sorted(p.stem for p in PAYLOADS_DIR.glob("*.json"))


def load_fixture(name: str) -> dict:
    """Load a payload fixture JSON file by name."""
    path = PAYLOADS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {name} (looked in {PAYLOADS_DIR})")
    return json.loads(path.read_text())


def list_scenarios() -> list[dict]:
    """List available scenarios with name and description."""
    results = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        results.append(
            {"name": data.get("name", path.stem), "description": data.get("description", "")}
        )
    return results


def load_scenario(name: str) -> dict:
    """Load a scenario JSON file by name."""
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {name} (looked in {SCENARIOS_DIR})")
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------


def _resolve_templates(
    params: dict,
    *,
    from_number: str = DEFAULT_FROM,
    to_number: str = DEFAULT_TO,
    profile_name: str = DEFAULT_PROFILE,
    body: str = "",
    media_url: str = DEFAULT_MEDIA_URL,
) -> dict:
    """Replace {{ var }} placeholders in fixture values."""
    sid = secrets.token_hex(16)
    wa_id = re.sub(r"[^\d]", "", from_number)

    replacements = {
        "sid": sid,
        "from": from_number,
        "to": to_number,
        "wa_id": wa_id,
        "profile_name": profile_name,
        "body": body,
        "media_url": media_url,
    }

    resolved = {}
    for key, value in params.items():
        if isinstance(value, str):
            for var, repl in replacements.items():
                value = value.replace("{{ " + var + " }}", repl)
        resolved[key] = value
    return resolved


# ---------------------------------------------------------------------------
# Payload building
# ---------------------------------------------------------------------------


def build_payload(
    fixture_name: str,
    overrides: dict | None = None,
    *,
    from_number: str = DEFAULT_FROM,
    to_number: str = DEFAULT_TO,
    profile_name: str = DEFAULT_PROFILE,
    body: str = "",
    media_url: str = DEFAULT_MEDIA_URL,
) -> dict:
    """Load a fixture, resolve templates, apply overrides."""
    params = load_fixture(fixture_name)
    params = _resolve_templates(
        params,
        from_number=from_number,
        to_number=to_number,
        profile_name=profile_name,
        body=body,
        media_url=media_url,
    )
    if overrides:
        params.update(overrides)
    return params


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------


def compute_signature(url: str, params: dict, token: str) -> str:
    """Compute X-Twilio-Signature using the Twilio SDK validator."""
    validator = RequestValidator(token)
    return validator.compute_signature(url, params)


# ---------------------------------------------------------------------------
# HTTP send
# ---------------------------------------------------------------------------


def send(
    url: str,
    params: dict,
    *,
    token: str = DEFAULT_TOKEN,
    no_signature: bool = False,
    verbose: bool = False,
) -> SimResult:
    """POST form-encoded params to the webhook URL and parse the TwiML response."""
    # Ensure the URL includes the webhook path
    webhook_url = url.rstrip("/")
    if not webhook_url.endswith("/webhook/twilio"):
        webhook_url += "/webhook/twilio"

    encoded = urllib.parse.urlencode(params).encode("utf-8")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if not no_signature:
        sig = compute_signature(webhook_url, params, token)
        headers["X-Twilio-Signature"] = sig

    if verbose:
        print(f"\n  \033[0;36m→ POST {webhook_url}\033[0m")
        sig_val = headers.get("X-Twilio-Signature", "(none)")
        print(f"  \033[0;36m  X-Twilio-Signature: {sig_val}\033[0m")
        for k, v in sorted(params.items()):
            display = v if len(str(v)) < 80 else str(v)[:77] + "..."
            print(f"  \033[0;36m  {k}: {display}\033[0m")

    req = urllib.request.Request(webhook_url, data=encoded, headers=headers)

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = resp.read().decode("utf-8")
        status = resp.status

        if verbose:
            print(f"  \033[0;32m← {status}\033[0m")
            print(f"  \033[0;32m  {body[:500]}\033[0m")

        messages = parse_twiml(body) if "xml" in resp.headers.get("Content-Type", "") else []
        return SimResult(status=status, body=body, messages=messages)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        if verbose:
            print(f"  \033[0;31m← {e.code} {body[:200]}\033[0m")
        return SimResult(status=e.code, body=body, ok=False)

    except urllib.error.URLError as e:
        return SimResult(status=0, body=str(e.reason), ok=False)


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------


class Colors:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    DIM = "\033[0;90m"
    RESET = "\033[0m"


def run_scenario(
    name: str,
    *,
    url: str,
    from_number: str = DEFAULT_FROM,
    to_number: str = DEFAULT_TO,
    profile_name: str = DEFAULT_PROFILE,
    token: str = DEFAULT_TOKEN,
    no_signature: bool = False,
    verbose: bool = False,
    delay: float = 1.0,
    json_output: bool = False,
) -> dict:
    """Run a named scenario — returns {"ok": bool, "steps": [...]}."""
    import time

    scenario = load_scenario(name)
    steps = scenario.get("steps", [])
    results: list[dict] = []
    all_pass = True

    if not json_output:
        print(f"\n{Colors.CYAN}▸ Scenario: {scenario.get('name', name)}{Colors.RESET}")
        print(f"  {scenario.get('description', '')}\n")

    for i, step in enumerate(steps):
        fixture = step.get("payload", "text_message")
        overrides = step.get("overrides", {})
        expects = step.get("expect_contains", [])
        desc = step.get("description", f"Step {i + 1}")

        payload = build_payload(
            fixture,
            overrides,
            from_number=from_number,
            to_number=to_number,
            profile_name=profile_name,
            body=overrides.get("Body", ""),
        )

        result = send(
            url,
            payload,
            token=token,
            no_signature=no_signature,
            verbose=verbose,
        )

        # Check expectations
        response_text = ""
        if result.messages:
            response_text = " ".join(m["body"] for m in result.messages)

        passed = result.ok
        failed_expects: list[str] = []
        for expect in expects:
            if expect.lower() not in response_text.lower():
                passed = False
                failed_expects.append(expect)

        if not passed:
            all_pass = False

        step_result = {
            "step": i + 1,
            "description": desc,
            "status": result.status,
            "passed": passed,
            "response_text": response_text[:500],
        }
        if failed_expects:
            step_result["missing"] = failed_expects
        results.append(step_result)

        if not json_output:
            status = (
                f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
            )
            print(f"  {status}  {desc}")
            if result.messages:
                print(format_messages(result.messages))
            elif not result.ok:
                print(f"    {Colors.RED}HTTP {result.status}: {result.body[:200]}{Colors.RESET}")
            if failed_expects:
                print(f"    {Colors.RED}Missing: {', '.join(failed_expects)}{Colors.RESET}")
            print()

        if i < len(steps) - 1 and delay > 0:
            time.sleep(delay)

    if not json_output:
        summary = (
            f"{Colors.GREEN}All steps passed{Colors.RESET}"
            if all_pass
            else f"{Colors.RED}Some steps failed{Colors.RESET}"
        )
        print(f"  {summary}\n")

    return {"ok": all_pass, "scenario": name, "steps": results}
