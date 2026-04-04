"""Development-only seed data router.

Routes:
- POST /api/dev/seed  Seed mock data for local testing
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from classgen.data import (
    add_teacher_class,
    save_homework_code,
    save_teacher,
)

router = APIRouter()


@router.post("/api/dev/seed")
async def dev_seed():
    """Seed mock data for local testing. Only works without Supabase."""
    from classgen.data.client import supabase as _sb

    if _sb:
        return JSONResponse(
            {"error": "Only available in local dev mode"}, status_code=403
        )

    # Seed a teacher
    teacher = save_teacher("+2348012345678", "Mrs. Okafor", "Lagos Model School")
    add_teacher_class("+2348012345678", "SS2 Biology")
    add_teacher_class("+2348012345678", "SS1 Mathematics")

    # Seed a homework code linked to the teacher
    code = "TEST01"
    quiz = [
        {
            "question": "What gas do plants absorb during photosynthesis?",
            "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide", "D) Hydrogen"],
            "correct": 2,
        },
        {
            "question": "Where in the leaf does photosynthesis mainly occur?",
            "options": ["A) Roots", "B) Stem", "C) Chloroplasts", "D) Bark"],
            "correct": 2,
        },
        {
            "question": "What is the green pigment in leaves called?",
            "options": ["A) Melanin", "B) Chlorophyll", "C) Haemoglobin", "D) Keratin"],
            "correct": 1,
        },
        {
            "question": "What is the main product of photosynthesis?",
            "options": ["A) Protein", "B) Starch", "C) Glucose", "D) Fat"],
            "correct": 2,
        },
        {
            "question": "Which of these is NOT needed for photosynthesis?",
            "options": ["A) Sunlight", "B) Water", "C) Soil", "D) Carbon dioxide"],
            "correct": 2,
        },
    ]
    hw_block = (
        "Title: The Plant Engineer's Report\n"
        "Summary: Story problem\n"
        "Details: You are a botanist hired by a village "
        "to explain why their crops are dying."
    )
    save_homework_code(
        code,
        "dev_seed",
        "Mock lesson content",
        quiz,
        hw_block,
        teacher_phone="+2348012345678",
    )
    return {
        "seeded": code,
        "teacher_slug": teacher.get("slug"),
        "quiz_questions": len(quiz),
    }
