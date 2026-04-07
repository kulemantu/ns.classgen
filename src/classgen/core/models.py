"""Pydantic domain models for ClassGen lesson packs.

Pure data — no I/O, no framework imports. These models represent the
structured JSON output from the LLM (V4.1+) and serve as the canonical
data format passed between services, adapters, and storage.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------


class KeyTerm(BaseModel):
    term: str
    definition: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct: int = Field(ge=0, le=3)
    explanation: str = ""


class HomeworkTask(BaseModel):
    id: str
    instruction: str
    type: str = ""  # real_world | calculation | comprehension | creative | observation
    clue: str = ""
    exercise_book_format: str = ""


# ---------------------------------------------------------------------------
# Block types (discriminated on "type" field)
# ---------------------------------------------------------------------------


class OpenerBlock(BaseModel):
    type: Literal["opener"] = "opener"
    title: str
    body: str
    format: str = ""  # what_if | demonstration | challenge | story_cold_open
    duration_minutes: int = 2
    props: list[str] = []


class ExplainBlock(BaseModel):
    type: Literal["explain"] = "explain"
    title: str
    body: str
    wow_fact: str = ""
    analogy: str = ""
    key_terms: list[KeyTerm] = []
    equation: str | None = None


class ActivityBlock(BaseModel):
    type: Literal["activity"] = "activity"
    title: str
    body: str
    format: str = ""  # relay_race | group_challenge | debate | etc.
    group_size: int = 5
    duration_minutes: int = 12
    materials: list[str] = []
    rules: list[str] = []
    expected_outcome: str = ""


class HomeworkBlock(BaseModel):
    type: Literal["homework"] = "homework"
    title: str
    body: str = ""
    format: str = ""  # adventure | investigation | creative | etc.
    narrative: str = ""
    tasks: list[HomeworkTask] = []
    completion: str = ""
    assessment_tip: str = ""
    quiz: list[QuizQuestion] = []


class TeacherNotesBlock(BaseModel):
    type: Literal["teacher_notes"] = "teacher_notes"
    title: str = "Teacher Notes"
    body: str = ""
    expected_answers: list[str] = []
    common_mistakes: list[str] = []
    quick_assessment: str = ""
    next_lesson_link: str = ""
    exam_tip: str = ""
    safety_notes: str | None = None


# Discriminated union — Pydantic v2 resolves the correct block type from "type".
Block = Annotated[
    Union[OpenerBlock, ExplainBlock, ActivityBlock, HomeworkBlock, TeacherNotesBlock],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Top-level lesson pack
# ---------------------------------------------------------------------------


class LessonMeta(BaseModel):
    subject: str = ""
    topic: str = ""
    class_level: str = ""
    exam_board: str = "WAEC"
    duration_minutes: int = 40
    language: str = "en"
    bilingual: str | None = None


class LessonPack(BaseModel):
    version: str = "4.0"
    meta: LessonMeta = Field(default_factory=LessonMeta)
    blocks: list[Block] = []
