"""School admin dashboard router.

Routes:
- GET /s/{slug}         School admin page (Jinja2 template)
- GET /s/{slug}/export  CSV export of school-wide quiz data
"""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

from classgen.data import (
    count_quiz_submissions_for_codes,
    get_quiz_results,
    get_school,
    get_school_teachers,
    list_homework_codes_for_teacher,
)

router = APIRouter()

# The Jinja2Templates instance is injected by app.py after creation.
templates: Jinja2Templates | None = None


@router.get("/s/{slug}", response_class=HTMLResponse)
async def school_admin(request: Request, slug: str):
    """School admin dashboard."""
    school = get_school(slug)
    if not school:
        return HTMLResponse("<h1>School not found</h1>", status_code=404)

    teachers = get_school_teachers(slug)
    # Enrich with lesson counts
    all_code_ids: list[str] = []
    for t in teachers:
        codes = list_homework_codes_for_teacher(t.get("phone", ""), limit=100)
        t["lesson_count"] = len(codes)
        all_code_ids.extend(hw.get("code", "") for hw in codes if hw.get("code"))

    total_lessons = sum(t.get("lesson_count", 0) for t in teachers)
    total_students = count_quiz_submissions_for_codes(all_code_ids)

    return templates.TemplateResponse(  # type: ignore[union-attr]
        request,
        "admin.html",
        {
            "school": school,
            "teachers": teachers,
            "total_lessons": total_lessons,
            "total_students": total_students,
        },
    )


@router.get("/s/{slug}/export")
async def school_export(slug: str):
    """Export school-wide data as CSV."""
    school = get_school(slug)
    if not school:
        return JSONResponse({"error": "School not found"}, status_code=404)

    teachers = get_school_teachers(slug)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Teacher",
            "Classes",
            "Homework Code",
            "Student",
            "Class",
            "Score",
            "Total",
            "Submitted",
        ]
    )

    for t in teachers:
        phone = t.get("phone", "")
        teacher_name = t.get("name", "")
        classes = ", ".join(t.get("classes", []))
        codes_raw = list_homework_codes_for_teacher(phone, limit=100)

        for hw in codes_raw:
            code = hw.get("code", "")
            submissions = get_quiz_results(code)
            if submissions:
                for s in submissions:
                    writer.writerow(
                        [
                            teacher_name,
                            classes,
                            code,
                            s.get("student_name", ""),
                            s.get("student_class", ""),
                            s.get("score", 0),
                            s.get("total", 0),
                            s.get("created_at", ""),
                        ]
                    )
            else:
                writer.writerow([teacher_name, classes, code, "", "", "", "", ""])

    csv_content = output.getvalue()
    school_name = school.get("name", "school").replace(" ", "_")
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{school_name}_export.csv"'
        },
    )
