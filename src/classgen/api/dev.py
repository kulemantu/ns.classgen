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
        return JSONResponse({"error": "Only available in local dev mode"}, status_code=403)

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

    # V4.2a — also seed a structured-format code so the new homework UI can be
    # exercised in the browser without an LLM call. Same teacher, different code.
    adv_code = "ADV001"
    adv_quiz = quiz[:2]
    adv_lesson_json = {
        "version": 1,
        "meta": {"subject": "Biology", "topic": "Photosynthesis", "class_level": "SS2"},
        "blocks": [
            {
                "type": "homework",
                "title": "The Oxygen Detective Case",
                "format": "detective",
                "narrative": (
                    "A village's biggest tree is dying. Three witnesses report "
                    "what they saw last week. Your job: gather evidence and write "
                    "a detective report explaining what's killing the tree using "
                    "what you learned about photosynthesis."
                ),
                "tasks": [
                    {
                        "id": "t1",
                        "instruction": "Visit one tree near your home. Sketch it in your exercise book.",
                        "type": "draw",
                        "exercise_book_format": "1 full page sketch + labels",
                        "clue": "Notice which side faces the sun.",
                    },
                    {
                        "id": "t2",
                        "instruction": "Cover one leaf with paper for 2 days. Compare to an uncovered leaf.",
                        "type": "experiment",
                        "exercise_book_format": "Before/after drawing + one paragraph",
                        "clue": "Photosynthesis needs light.",
                    },
                    {
                        "id": "t3",
                        "instruction": "Write a 1-paragraph detective report naming the most likely cause.",
                        "type": "write",
                        "exercise_book_format": "150-200 words",
                    },
                ],
                "completion": "Bring your exercise book to class on Monday. We'll compare findings.",
            }
        ],
    }
    save_homework_code(
        adv_code,
        "dev_seed_adv",
        "Mock structured lesson content",
        adv_quiz,
        "Title: The Oxygen Detective Case\nDetails: see structured payload",
        teacher_phone="+2348012345678",
        lesson_json=adv_lesson_json,
    )

    return {
        "seeded": [code, adv_code],
        "teacher_slug": teacher.get("slug"),
        "quiz_questions": len(quiz),
    }
