"""Tests for status change Input DTOs."""

import pytest

from taskdog_core.application.dto.single_task_inputs import (
    CancelTaskInput,
    CompleteTaskInput,
    PauseTaskInput,
    ReopenTaskInput,
    StartTaskInput,
)


class TestStatusChangeInputs:
    """Test suite for all status change Input DTOs."""

    @pytest.mark.parametrize(
        "dto_class",
        [
            StartTaskInput,
            CompleteTaskInput,
            PauseTaskInput,
            CancelTaskInput,
            ReopenTaskInput,
        ],
        ids=["start", "complete", "pause", "cancel", "reopen"],
    )
    def test_create_with_task_id(self, dto_class):
        """Test creating DTO with task_id."""
        dto = dto_class(task_id=1)

        assert dto.task_id == 1

    @pytest.mark.parametrize(
        "dto_class",
        [
            StartTaskInput,
            CompleteTaskInput,
            PauseTaskInput,
            CancelTaskInput,
            ReopenTaskInput,
        ],
        ids=["start", "complete", "pause", "cancel", "reopen"],
    )
    def test_equality(self, dto_class):
        """Test equality comparison."""
        dto1 = dto_class(task_id=1)
        dto2 = dto_class(task_id=1)
        dto3 = dto_class(task_id=2)

        assert dto1 == dto2
        assert dto1 != dto3

    def test_start_task_input_repr(self) -> None:
        """Test repr includes task_id for StartTaskInput."""
        dto = StartTaskInput(task_id=42)
        repr_str = repr(dto)

        assert "task_id=42" in repr_str
