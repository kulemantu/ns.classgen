"""Cross-channel parity comparison — web vs WhatsApp."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ParityCheck:
    name: str
    passed: bool
    web_value: str = ""
    wa_value: str = ""
    note: str = ""


@dataclass
class ParityResult:
    test_name: str
    web_transcript: str = ""
    whatsapp_transcript: str = ""
    checks: list[ParityCheck] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    all_passed: bool = True

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = directory / f"{ts}_{self.test_name}_parity.json"
        path.write_text(self.to_json())
        return path


def compare_responses(
    test_name: str,
    web_data: dict,
    wa_data: dict,
    check_names: list[str] | None = None,
) -> ParityResult:
    """Compare web and WhatsApp results for parity.

    web_data: {reply, pdf_url, homework_code, blocks, status, duration_ms}
    wa_data:  {messages, status, duration_ms, has_pdf_media}
    """
    checks: list[ParityCheck] = []
    gaps: list[str] = []

    available_checks = {
        "response_ok": _check_response_ok,
        "homework_code": _check_homework_code,
        "pdf_available": _check_pdf_available,
        "has_content": _check_has_content,
        "block_count": _check_block_count,
    }

    to_run = check_names or list(available_checks.keys())

    for name in to_run:
        fn = available_checks.get(name)
        if fn:
            check, gap = fn(web_data, wa_data)
            checks.append(check)
            if gap:
                gaps.append(gap)

    all_passed = all(c.passed for c in checks)
    return ParityResult(
        test_name=test_name,
        checks=checks,
        gaps=gaps,
        all_passed=all_passed,
    )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_response_ok(web: dict, wa: dict) -> tuple[ParityCheck, str]:
    web_ok = web.get("status") == 200
    wa_ok = wa.get("status") == 200
    return (
        ParityCheck(
            name="response_ok",
            passed=web_ok and wa_ok,
            web_value=str(web.get("status")),
            wa_value=str(wa.get("status")),
            note="Both channels should return 200",
        ),
        "" if web_ok and wa_ok else "One or both channels returned non-200",
    )


def _check_homework_code(web: dict, wa: dict) -> tuple[ParityCheck, str]:
    web_code = web.get("homework_code") or ""
    wa_code = wa.get("homework_code") or ""
    both_present = bool(web_code) and bool(wa_code)
    return (
        ParityCheck(
            name="homework_code",
            passed=both_present,
            web_value=web_code or "(none)",
            wa_value=wa_code or "(none)",
            note="Both channels should generate a homework code",
        ),
        "" if both_present else "Homework code missing from one channel",
    )


def _check_pdf_available(web: dict, wa: dict) -> tuple[ParityCheck, str]:
    web_pdf = bool(web.get("pdf_url"))
    wa_pdf = bool(wa.get("has_pdf_media"))
    both = web_pdf and wa_pdf
    gap = ""
    if web_pdf and not wa_pdf:
        gap = "Web has PDF but WhatsApp does not attach it as media"
    elif wa_pdf and not web_pdf:
        gap = "WhatsApp has PDF media but web does not return pdf_url"
    return (
        ParityCheck(
            name="pdf_available",
            passed=both,
            web_value="yes" if web_pdf else "no",
            wa_value="yes" if wa_pdf else "no",
            note="Both channels should make PDF available",
        ),
        gap,
    )


def _check_has_content(web: dict, wa: dict) -> tuple[ParityCheck, str]:
    web_has = bool(web.get("reply"))
    wa_has = bool(wa.get("messages"))
    both = web_has and wa_has
    return (
        ParityCheck(
            name="has_content",
            passed=both,
            web_value=f"{len(web.get('reply', ''))} chars" if web_has else "empty",
            wa_value=f"{len(wa.get('messages', []))} messages" if wa_has else "empty",
            note="Both channels should return content",
        ),
        "" if both else "One channel returned empty content",
    )


def _check_block_count(web: dict, wa: dict) -> tuple[ParityCheck, str]:
    web_blocks = len(web.get("blocks", []))
    wa_blocks = wa.get("block_count", 0)
    match = web_blocks == wa_blocks if web_blocks > 0 else True
    gap = ""
    if web_blocks > 0 and wa_blocks == 0:
        gap = "Web returns structured blocks; WhatsApp summary doesn't expose block count"
    return (
        ParityCheck(
            name="block_count",
            passed=match,
            web_value=str(web_blocks),
            wa_value=str(wa_blocks),
            note="Block count should match between channels",
        ),
        gap,
    )


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------


def print_parity_result(result: ParityResult) -> None:
    """Print parity result to terminal."""
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    RESET = "\033[0m"

    status = f"{GREEN}PASS{RESET}" if result.all_passed else f"{RED}FAIL{RESET}"
    print(f"\n{CYAN}Parity: {result.test_name}{RESET}  {status}\n")

    for check in result.checks:
        icon = f"{GREEN}\u2713{RESET}" if check.passed else f"{RED}\u2717{RESET}"
        print(f"  {icon} {check.name}")
        print(f"      Web: {check.web_value}  |  WA: {check.wa_value}")
        if not check.passed:
            print(f"      {RED}{check.note}{RESET}")

    if result.gaps:
        print(f"\n  {CYAN}Gaps:{RESET}")
        for gap in result.gaps:
            print(f"    \u2022 {gap}")
    print()
