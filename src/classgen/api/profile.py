"""Teacher public profile router.

Routes:
- GET /t/{slug}         Teacher profile page (Jinja2 template)
- GET /t/{slug}/export  CSV export of teacher's quiz data
"""

from __future__ import annotations

import csv
import io
import re
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

from classgen.data import (
    get_quiz_results,
    get_teacher_by_slug,
    get_teacher_lesson_stats,
    list_homework_codes_for_teacher,
)

router = APIRouter()

# The Jinja2Templates instance is injected by app.py after creation.
templates: Jinja2Templates | None = None


@router.get("/t/{slug}", response_class=HTMLResponse)
async def teacher_profile(request: Request, slug: str):
    """Public teacher profile page."""
    teacher = get_teacher_by_slug(slug)
    if not teacher:
        return HTMLResponse("<h1>Teacher not found</h1>", status_code=404)

    phone = teacher.get("phone", "")
    codes_raw = list_homework_codes_for_teacher(phone, limit=10)
    codes = []
    for hw in codes_raw:
        block = hw.get("homework_block", "")
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", block)
        codes.append(
            {
                "code": hw.get("code", ""),
                "title": title_match.group(1).strip() if title_match else "Homework",
            }
        )

    stats = get_teacher_lesson_stats(phone)

    return templates.TemplateResponse(  # type: ignore[union-attr]
        request,
        "profile.html",
        {
            "teacher": teacher,
            "codes": codes,
            "stats": stats,
        },
    )


@router.get("/t/{slug}/export")
async def teacher_export(slug: str):
    """Export teacher's quiz data as CSV."""
    teacher = get_teacher_by_slug(slug)
    if not teacher:
        return JSONResponse({"error": "Teacher not found"}, status_code=404)

    phone = teacher.get("phone", "")
    codes_raw = list_homework_codes_for_teacher(phone, limit=100)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Homework Code",
            "Homework Title",
            "Student",
            "Class",
            "Score",
            "Total",
            "Submitted",
        ]
    )

    for hw in codes_raw:
        code = hw.get("code", "")
        block = hw.get("homework_block", "")
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", block)
        title = title_match.group(1).strip() if title_match else "Homework"

        submissions = get_quiz_results(code)
        if submissions:
            for s in submissions:
                writer.writerow(
                    [
                        code,
                        title,
                        s.get("student_name", ""),
                        s.get("student_class", ""),
                        s.get("score", 0),
                        s.get("total", 0),
                        s.get("created_at", ""),
                    ]
                )
        else:
            writer.writerow([code, title, "", "", "", "", ""])

    csv_content = output.getvalue()
    teacher_name = teacher.get("name", "teacher").replace(" ", "_")
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{teacher_name}_export.csv"'},
    )
