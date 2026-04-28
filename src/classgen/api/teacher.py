"""Teacher profile API router.

Routes:
- GET    /api/teacher/profile
- POST   /api/teacher/register
- PATCH  /api/teacher/profile
- POST   /api/teacher/classes
- DELETE /api/teacher/classes/{class_name}
- DELETE /api/teacher/history
- GET    /api/teacher/homework
"""

from __future__ import annotations

import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from classgen.api.schemas import (
    TeacherClassRequest,
    TeacherCountryRequest,
    TeacherRegisterRequest,
    TeacherUpdateRequest,
)
from classgen.data import (
    add_teacher_class,
    clear_session_history,
    get_teacher_by_phone,
    get_teacher_lesson_stats,
    list_homework_codes_for_teacher,
    remove_teacher_class,
    save_teacher,
    update_teacher_country,
    update_teacher_name,
)
from classgen.data.countries import list_grouped as list_countries_grouped

router = APIRouter()


@router.get("/api/teacher/profile")
async def teacher_profile_api(thread_id: str = ""):
    """Get teacher profile, stats, and recent codes for a web teacher."""
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)
    teacher = get_teacher_by_phone(thread_id)
    if not teacher:
        return {"registered": False}
    stats = get_teacher_lesson_stats(thread_id)
    codes_raw = list_homework_codes_for_teacher(thread_id, limit=10)
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
    return {
        "registered": True,
        "teacher": {
            "name": teacher.get("name", ""),
            "slug": teacher.get("slug", ""),
            "classes": teacher.get("classes", []),
            "country": teacher.get("country", ""),
        },
        "stats": stats,
        "codes": codes,
    }


@router.post("/api/teacher/register")
async def teacher_register_api(req: TeacherRegisterRequest):
    """Register a web teacher using their threadId as identity."""
    teacher = save_teacher(req.thread_id, req.name, country=req.country)
    return {
        "registered": True,
        "teacher": {
            "name": teacher.get("name", ""),
            "slug": teacher.get("slug", ""),
            "classes": teacher.get("classes", []),
            "country": teacher.get("country", ""),
        },
    }


@router.patch("/api/teacher/profile")
async def teacher_update_api(req: TeacherUpdateRequest):
    """Update a web teacher's name."""
    teacher = update_teacher_name(req.thread_id, req.name)
    if not teacher:
        return JSONResponse({"error": "Teacher not found"}, status_code=404)
    return {
        "teacher": {
            "name": teacher.get("name", ""),
            "slug": teacher.get("slug", ""),
            "classes": teacher.get("classes", []),
            "country": teacher.get("country", ""),
        },
    }


@router.patch("/api/teacher/country")
async def teacher_update_country_api(req: TeacherCountryRequest):
    """Update a web teacher's country."""
    teacher = update_teacher_country(req.thread_id, req.country)
    if not teacher:
        return JSONResponse({"error": "Teacher not found"}, status_code=404)
    return {"country": teacher.get("country", "")}


@router.get("/api/teacher/countries")
async def teacher_countries_api():
    """List supported countries for the dropdown, grouped by region.

    Returns ``{"groups": [{"region", "countries": [{"name", "flag"}]}]}``.
    ``flag`` is presentation only — the teacher's stored country (DB
    column / LLM prompt) is always the plain ``name`` string.
    """
    return {"groups": list_countries_grouped()}


@router.post("/api/teacher/classes")
async def teacher_add_class_api(req: TeacherClassRequest):
    """Add a class to a web teacher's profile."""
    teacher = get_teacher_by_phone(req.thread_id)
    if not teacher:
        return JSONResponse({"error": "Register first"}, status_code=404)
    add_teacher_class(req.thread_id, req.class_name)
    updated = get_teacher_by_phone(req.thread_id)
    return {"classes": updated.get("classes", []) if updated else []}


@router.delete("/api/teacher/classes/{class_name}")
async def teacher_remove_class_api(class_name: str, thread_id: str = ""):
    """Remove a class from a web teacher's profile."""
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)
    teacher = get_teacher_by_phone(thread_id)
    if not teacher:
        return JSONResponse({"error": "Teacher not found"}, status_code=404)
    remove_teacher_class(thread_id, class_name)
    updated = get_teacher_by_phone(thread_id)
    return {"classes": updated.get("classes", []) if updated else []}


@router.delete("/api/teacher/history")
async def teacher_clear_history_api(thread_id: str = ""):
    """Clear chat history for a web teacher's thread."""
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)
    clear_session_history(thread_id)
    return {"ok": True}


@router.get("/api/teacher/homework")
async def teacher_homework_api(thread_id: str = ""):
    """List homework codes for a teacher."""
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)
    teacher = get_teacher_by_phone(thread_id)
    if not teacher:
        return JSONResponse({"error": "Teacher not found"}, status_code=404)
    codes_raw = list_homework_codes_for_teacher(thread_id, limit=50)
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
    return {"codes": codes}
