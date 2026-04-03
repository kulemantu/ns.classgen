"""Pydantic request/response models for the ClassGen API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str


class QuizSubmission(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    student_class: str = Field(..., min_length=1, max_length=50)
    answers: list[int]


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict
    teacher_id: str = ""  # thread_id or phone


class TeacherRegisterRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=2, max_length=100)


class TeacherUpdateRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=2, max_length=100)


class TeacherClassRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    class_name: str = Field(..., min_length=3, max_length=50)
