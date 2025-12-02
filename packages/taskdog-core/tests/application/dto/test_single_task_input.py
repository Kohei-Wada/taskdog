"""Tests for SingleTaskInput and its type aliases."""

import pytest

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.single_task_inputs import (
    ArchiveTaskInput,
    CompleteTaskInput,
    PauseTaskInput,
    RemoveTaskInput,
    StartTaskInput,
)


class TestSingleTaskInput:
    """Test cases for SingleTaskInput base class."""

    def test_instantiation_with_task_id(self):
        """Test SingleTaskInput can be instantiated with task_id."""
        dto = SingleTaskInput(task_id=123)
        assert dto.task_id == 123

    def test_task_id_field_accessible(self):
        """Test task_id field is accessible."""
        dto = SingleTaskInput(task_id=456)
        assert isinstance(dto.task_id, int)
        assert dto.task_id == 456


class TestTypeAliases:
    """Test cases for type aliases of SingleTaskInput."""

    @pytest.mark.parametrize(
        "dto_class,task_id",
        [
            (StartTaskInput, 1),
            (CompleteTaskInput, 2),
            (PauseTaskInput, 3),
            (RemoveTaskInput, 4),
            (ArchiveTaskInput, 5),
        ],
        ids=[
            "start_task_input",
            "complete_task_input",
            "pause_task_input",
            "remove_task_input",
            "archive_task_input",
        ],
    )
    def test_alias_is_single_task_input(self, dto_class, task_id):
        """Test that type alias is an instance of SingleTaskInput."""
        dto = dto_class(task_id=task_id)
        assert isinstance(dto, SingleTaskInput)
        assert dto.task_id == task_id

    def test_all_aliases_are_same_type(self):
        """Test all type aliases resolve to the same type."""
        assert StartTaskInput == SingleTaskInput
        assert CompleteTaskInput == SingleTaskInput
        assert PauseTaskInput == SingleTaskInput
        assert RemoveTaskInput == SingleTaskInput
        assert ArchiveTaskInput == SingleTaskInput

    def test_aliases_can_be_used_interchangeably(self):
        """Test type aliases can be used interchangeably."""
        dto1 = StartTaskInput(task_id=10)
        dto2 = CompleteTaskInput(task_id=10)
        dto3 = SingleTaskInput(task_id=10)

        # All should have the same task_id value
        assert dto1.task_id == dto2.task_id
        assert dto2.task_id == dto3.task_id

        # All should be instances of SingleTaskInput
        assert isinstance(dto1, SingleTaskInput)
        assert isinstance(dto2, SingleTaskInput)
        assert isinstance(dto3, SingleTaskInput)
