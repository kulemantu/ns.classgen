"""Homework and quiz API router.

Routes:
- GET  /h/{code}             Serve homework quiz page
- GET  /api/h/{code}         Homework data JSON
- POST /h/{code}/submit      Grade + store quiz submission
- GET  /h/{code}/results     Serve teacher results page
- GET  /api/h/{code}/results Results data JSON
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from classgen.api.schemas import QuizSubmission
from classgen.data import (
    get_homework_code,
    get_quiz_results,
    save_quiz_submission,
)
from classgen.integrations.twilio import send_quiz_summary
from classgen.services.notification_service import notify_quiz_submission

router = APIRouter()

_APP_ROOT = Path(os.environ.get("APP_ROOT", str(Path(__file__).resolve().parents[3])))


@router.get("/h/{code}", response_class=HTMLResponse)
async def homework_page(code: str):
    """Serve the lightweight quiz page for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return HTMLResponse(
            "<h1>Homework code not found</h1><p>Check the code and try again.</p>",
            status_code=404,
        )
    homework_path = _APP_ROOT / "homework.html"
    if not homework_path.exists():
        return HTMLResponse("<h1>Quiz page not available</h1>", status_code=500)
    return FileResponse(str(homework_path))


@router.get("/api/h/{code}")
async def homework_data(code: str):
    """Return homework data as JSON for the quiz page to consume."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "not_found"}, status_code=404)

    response: dict = {
        "code": hw["code"],
        "homework_block": hw["homework_block"],
        "quiz_questions": hw.get("quiz_questions", []),
    }

    # Include structured lesson data when available
    lesson_json = hw.get("lesson_json")
    if lesson_json and isinstance(lesson_json, dict):
        blocks = lesson_json.get("blocks", [])
        if isinstance(blocks, list):
            hw_block = next(
                (b for b in blocks if isinstance(b, dict) and b.get("type") == "homework"),
                None,
            )
            if hw_block:
                # Explicitly whitelist fields — never expose assessment_tip,
                # quiz answers, or teacher-facing data to students.
                tasks = hw_block.get("tasks", [])
                response["homework_structured"] = {
                    "title": str(hw_block.get("title", "")),
                    "narrative": str(hw_block.get("narrative", "")),
                    "tasks": tasks if isinstance(tasks, list) else [],
                    "format": str(hw_block.get("format", "")),
                    "completion": str(hw_block.get("completion", "")),
                }

    return response


@router.post("/h/{code}/submit")
async def submit_quiz(request: Request, code: str, submission: QuizSubmission):
    """Grade and store a student's quiz submission."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "Homework code not found"}, status_code=404)

    questions = hw.get("quiz_questions", [])
    if not questions:
        return JSONResponse(
            {"error": "No quiz available for this code"}, status_code=400
        )

    total = len(questions)
    score = 0
    results = []
    for i, q in enumerate(questions):
        student_answer = submission.answers[i] if i < len(submission.answers) else -1
        correct = q.get("correct", -1)
        is_correct = student_answer == correct
        if is_correct:
            score += 1
        results.append(
            {
                "question": q["question"],
                "options": q["options"],
                "student_answer": student_answer,
                "correct": correct,
                "is_correct": is_correct,
            }
        )

    save_quiz_submission(
        code.upper(),
        submission.student_name,
        submission.student_class,
        submission.answers,
        score,
        total,
    )

    # Notify teacher via push notification
    teacher_phone = hw.get("teacher_phone", "")
    teacher_id = teacher_phone or hw.get("thread_id", "")
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    if teacher_id:
        notify_quiz_submission(
            teacher_id, code.upper(), submission.student_name, score, total, base_url
        )

    # Send WhatsApp summary at milestones (1st, 5th, 10th, then every 10th)
    if teacher_phone:
        submissions = get_quiz_results(code.upper())
        count = len(submissions)
        if count in (1, 5, 10) or (count > 10 and count % 10 == 0):
            avg = sum(s.get("score", 0) for s in submissions) / count
            send_quiz_summary(teacher_phone, code.upper(), count, avg, total, base_url)

    return {
        "score": score,
        "total": total,
        "results": results,
    }


@router.get("/h/{code}/results", response_class=HTMLResponse)
async def homework_results_page(code: str):
    """Serve the teacher results page for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return HTMLResponse(
            "<h1>Homework code not found</h1><p>Check the code and try again.</p>",
            status_code=404,
        )
    results_path = _APP_ROOT / "results.html"
    if not results_path.exists():
        return HTMLResponse("<h1>Results page not available</h1>", status_code=500)
    return FileResponse(str(results_path))


@router.get("/api/h/{code}/results")
async def homework_results_data(code: str):
    """Return quiz submission results for a homework code."""
    hw = get_homework_code(code.upper())
    if not hw:
        return JSONResponse({"error": "not_found"}, status_code=404)

    submissions = get_quiz_results(code.upper())
    total_submissions = len(submissions)
    avg_score = (
        sum(s.get("score", 0) for s in submissions) / total_submissions
        if total_submissions > 0
        else 0
    )

    # Per-question breakdown
    questions = hw.get("quiz_questions", [])
    question_stats = []
    for i, q in enumerate(questions):
        correct_count = sum(
            1
            for s in submissions
            if i < len(s.get("answers", [])) and s["answers"][i] == q.get("correct", -1)
        )
        question_stats.append(
            {
                "question": q["question"],
                "correct_count": correct_count,
                "total_attempts": total_submissions,
                "percent_correct": round(correct_count / total_submissions * 100)
                if total_submissions
                else 0,
            }
        )

    return {
        "code": code.upper(),
        "total_submissions": total_submissions,
        "average_score": round(avg_score, 1),
        "total_questions": len(questions),
        "submissions": [
            {
                "student_name": s.get("student_name"),
                "student_class": s.get("student_class"),
                "score": s.get("score"),
                "total": s.get("total"),
                "created_at": s.get("created_at"),
            }
            for s in submissions
        ],
        "question_stats": question_stats,
    }
