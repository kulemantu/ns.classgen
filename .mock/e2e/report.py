"""HTML parity report generator."""

from __future__ import annotations

import html
from pathlib import Path

from parity import ParityResult


def generate_html_report(result: ParityResult, output_dir: Path) -> Path:
    """Generate a self-contained HTML parity report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = output_dir / f"{ts}_{result.test_name}_parity.html"
    path.write_text(_render(result))
    return path


def _render(r: ParityResult) -> str:
    status_cls = "pass" if r.all_passed else "fail"
    status_text = "ALL CHECKS PASSED" if r.all_passed else "SOME CHECKS FAILED"

    checks_html = []
    for c in r.checks:
        cls = "pass" if c.passed else "fail"
        icon = "\u2713" if c.passed else "\u2717"
        checks_html.append(
            f'<tr class="{cls}">'
            f"<td>{icon}</td>"
            f"<td>{html.escape(c.name)}</td>"
            f"<td>{html.escape(c.web_value)}</td>"
            f"<td>{html.escape(c.wa_value)}</td>"
            f"<td>{html.escape(c.note)}</td>"
            f"</tr>"
        )

    gaps_html = ""
    if r.gaps:
        items = "".join(f"<li>{html.escape(g)}</li>" for g in r.gaps)
        gaps_html = f'<div class="gaps"><h3>Feature Gaps</h3><ul>{items}</ul></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parity: {html.escape(r.test_name)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 20px; }}
.container {{ max-width: 800px; margin: 0 auto; }}
.header {{ background: #1a237e; color: #fff; padding: 16px 20px; border-radius: 8px 8px 0 0; }}
.header h1 {{ font-size: 20px; }}
.header .status {{ margin-top: 4px; font-size: 14px; }}
.status.pass {{ color: #a5d6a7; }}
.status.fail {{ color: #ef9a9a; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }}
th {{ background: #e8eaf6; font-weight: 600; }}
tr.pass td:first-child {{ color: #2e7d32; font-weight: 700; }}
tr.fail td:first-child {{ color: #c62828; font-weight: 700; }}
.gaps {{ background: #fff3e0; padding: 16px 20px; border-radius: 0 0 8px 8px; }}
.gaps h3 {{ font-size: 16px; margin-bottom: 8px; }}
.gaps li {{ margin: 4px 0 4px 20px; font-size: 14px; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>Parity Report: {html.escape(r.test_name)}</h1>
  <div class="status {status_cls}">{status_text}</div>
</div>
<table>
  <thead><tr><th></th><th>Check</th><th>Web</th><th>WhatsApp</th><th>Note</th></tr></thead>
  <tbody>{"".join(checks_html)}</tbody>
</table>
{gaps_html}
</div>
</body>
</html>"""
