"""Tests for classgen.core.models — Pydantic lesson pack models."""

import pytest
from pydantic import ValidationError

from classgen.core.models import (
    ExplainBlock,
    HomeworkBlock,
    HomeworkTask,
    KeyTerm,
    LessonMeta,
    LessonPack,
    OpenerBlock,
    QuizQuestion,
    TeacherNotesBlock,
)
from tests.fixtures import SAMPLE_LESSON_JSON_DICT


class TestLessonPack:
    def test_from_valid_json(self):
        pack = LessonPack.model_validate(SAMPLE_LESSON_JSON_DICT)
        assert pack.version == "4.0"
        assert pack.meta.subject == "Biology"
        assert pack.meta.topic == "Photosynthesis"
        assert len(pack.blocks) == 5
        assert pack.blocks[0].type == "opener"
        assert pack.blocks[1].type == "explain"
        assert pack.blocks[2].type == "activity"
        assert pack.blocks[3].type == "homework"
        assert pack.blocks[4].type == "teacher_notes"

    def test_missing_optional_fields(self):
        data = {
            "blocks": [
                {"type": "opener", "title": "Test", "body": "Test body"},
                {"type": "explain", "title": "Test", "body": "Test body"},
            ]
        }
        pack = LessonPack.model_validate(data)
        assert pack.version == "4.0"
        assert pack.meta.exam_board == "WAEC"
        explain = pack.blocks[1]
        assert isinstance(explain, ExplainBlock)
        assert explain.equation is None
        assert explain.key_terms == []

    def test_empty_blocks(self):
        pack = LessonPack(blocks=[])
        assert pack.blocks == []

    def test_serialization_roundtrip(self):
        original = LessonPack.model_validate(SAMPLE_LESSON_JSON_DICT)
        dumped = original.model_dump()
        restored = LessonPack.model_validate(dumped)
        assert original == restored

    def test_discriminated_union_resolves_types(self):
        pack = LessonPack.model_validate(SAMPLE_LESSON_JSON_DICT)
        assert isinstance(pack.blocks[0], OpenerBlock)
        assert isinstance(pack.blocks[1], ExplainBlock)
        assert isinstance(pack.blocks[3], HomeworkBlock)
        assert isinstance(pack.blocks[4], TeacherNotesBlock)

    def test_invalid_block_type_rejected(self):
        data = {"blocks": [{"type": "unknown_type", "title": "Test", "body": "Test"}]}
        with pytest.raises(ValidationError):
            LessonPack.model_validate(data)


class TestQuizQuestion:
    def test_valid_question(self):
        q = QuizQuestion(
            question="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct=1,
        )
        assert q.correct == 1

    def test_correct_index_out_of_range(self):
        with pytest.raises(ValidationError):
            QuizQuestion(
                question="Test",
                options=["A", "B", "C", "D"],
                correct=4,
            )

    def test_too_few_options(self):
        with pytest.raises(ValidationError):
            QuizQuestion(
                question="Test",
                options=["A", "B"],
                correct=0,
            )

    def test_too_many_options(self):
        with pytest.raises(ValidationError):
            QuizQuestion(
                question="Test",
                options=["A", "B", "C", "D", "E"],
                correct=0,
            )


class TestHomeworkBlock:
    def test_with_tasks_and_quiz(self):
        pack = LessonPack.model_validate(SAMPLE_LESSON_JSON_DICT)
        hw = pack.blocks[3]
        assert isinstance(hw, HomeworkBlock)
        assert len(hw.tasks) == 2
        assert hw.tasks[0].id == "clue_1"
        assert hw.tasks[0].type == "real_world"
        assert len(hw.quiz) == 5
        assert hw.quiz[0].correct == 1

    def test_empty_tasks_and_quiz(self):
        hw = HomeworkBlock(title="Test Homework")
        assert hw.tasks == []
        assert hw.quiz == []


class TestTeacherNotesBlock:
    def test_safety_notes_nullable(self):
        tn = TeacherNotesBlock(safety_notes=None)
        assert tn.safety_notes is None

    def test_safety_notes_with_value(self):
        tn = TeacherNotesBlock(safety_notes="Requires outdoor visit")
        assert tn.safety_notes == "Requires outdoor visit"


class TestLessonMeta:
    def test_defaults(self):
        meta = LessonMeta()
        assert meta.exam_board == "WAEC"
        assert meta.duration_minutes == 40
        assert meta.language == "en"
        assert meta.bilingual is None

    def test_bilingual(self):
        meta = LessonMeta(bilingual="yo")
        assert meta.bilingual == "yo"


class TestSupportingTypes:
    def test_key_term(self):
        kt = KeyTerm(term="chlorophyll", definition="Green pigment")
        assert kt.term == "chlorophyll"

    def test_homework_task(self):
        task = HomeworkTask(id="t1", instruction="Do something")
        assert task.type == ""
        assert task.clue == ""
