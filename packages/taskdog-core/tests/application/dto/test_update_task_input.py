"""Tests for UpdateTaskInput DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.domain.entities.task import TaskStatus


class TestUpdateTaskInput:
    """Test suite for UpdateTaskInput DTO."""

    def test_create_with_task_id_only(self) -> None:
        """Test creating DTO with only task_id (no updates)."""
        dto = UpdateTaskInput(task_id=1)

        assert dto.task_id == 1
        assert dto.name is None
        assert dto.priority is None
        assert dto.status is None
        assert dto.planned_start is None
        assert dto.planned_end is None
        assert dto.deadline is None
        assert dto.estimated_duration is None
        assert dto.is_fixed is None
        assert dto.tags is None

    def test_create_with_name_update(self) -> None:
        """Test creating DTO with name update."""
        dto = UpdateTaskInput(task_id=1, name="Updated Name")

        assert dto.task_id == 1
        assert dto.name == "Updated Name"

    def test_create_with_priority_update(self) -> None:
        """Test creating DTO with priority update."""
        dto = UpdateTaskInput(task_id=1, priority=5)

        assert dto.priority == 5

    def test_create_with_status_update(self) -> None:
        """Test creating DTO with status update."""
        dto = UpdateTaskInput(task_id=1, status=TaskStatus.IN_PROGRESS)

        assert dto.status == TaskStatus.IN_PROGRESS

    def test_create_with_datetime_updates(self) -> None:
        """Test creating DTO with datetime field updates."""
        planned_start = datetime(2025, 1, 1, 9, 0)
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = UpdateTaskInput(
            task_id=1,
            planned_start=planned_start,
            deadline=deadline,
        )

        assert dto.planned_start == planned_start
        assert dto.deadline == deadline

    def test_create_with_estimated_duration_update(self) -> None:
        """Test creating DTO with estimated duration update."""
        dto = UpdateTaskInput(task_id=1, estimated_duration=15.5)

        assert dto.estimated_duration == 15.5

    def test_create_with_is_fixed_update(self) -> None:
        """Test creating DTO with is_fixed update."""
        dto = UpdateTaskInput(task_id=1, is_fixed=True)

        assert dto.is_fixed is True

    def test_create_with_tags_update(self) -> None:
        """Test creating DTO with tags update."""
        dto = UpdateTaskInput(task_id=1, tags=["new", "tags"])

        assert dto.tags == ["new", "tags"]

    def test_create_with_all_fields(self) -> None:
        """Test creating DTO with all fields populated."""
        planned_start = datetime(2025, 1, 1, 9, 0)
        planned_end = datetime(2025, 1, 5, 18, 0)
        deadline = datetime(2025, 1, 10, 23, 59)

        dto = UpdateTaskInput(
            task_id=123,
            name="Complete Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=10.5,
            is_fixed=True,
            tags=["urgent", "backend"],
        )

        assert dto.task_id == 123
        assert dto.name == "Complete Task"
        assert dto.priority == 2
        assert dto.status == TaskStatus.COMPLETED
        assert dto.planned_start == planned_start
        assert dto.planned_end == planned_end
        assert dto.deadline == deadline
        assert dto.estimated_duration == 10.5
        assert dto.is_fixed is True
        assert dto.tags == ["urgent", "backend"]

    def test_create_with_empty_tags(self) -> None:
        """Test creating DTO with empty tags list."""
        dto = UpdateTaskInput(task_id=1, tags=[])

        assert dto.tags == []

    def test_create_with_zero_priority(self) -> None:
        """Test creating DTO with zero priority."""
        dto = UpdateTaskInput(task_id=1, priority=0)

        assert dto.priority == 0

    def test_equality_with_same_values(self) -> None:
        """Test that two DTOs with same values are equal."""
        dto1 = UpdateTaskInput(task_id=1, name="Task", priority=2)
        dto2 = UpdateTaskInput(task_id=1, name="Task", priority=2)

        assert dto1 == dto2

    def test_inequality_with_different_values(self) -> None:
        """Test that two DTOs with different values are not equal."""
        dto1 = UpdateTaskInput(task_id=1, name="Task 1")
        dto2 = UpdateTaskInput(task_id=1, name="Task 2")

        assert dto1 != dto2

    def test_create_with_unicode_name(self) -> None:
        """Test creating DTO with Unicode characters in name."""
        dto = UpdateTaskInput(task_id=1, name="更新されたタスク 🚀")

        assert dto.name == "更新されたタスク 🚀"

    def test_repr_includes_task_id(self) -> None:
        """Test that repr includes task_id."""
        dto = UpdateTaskInput(task_id=42, name="Test")
        repr_str = repr(dto)

        assert "task_id=42" in repr_str

    def test_can_update_single_field(self) -> None:
        """Test that single field can be updated while others remain None."""
        dto = UpdateTaskInput(task_id=1, deadline=datetime(2025, 6, 1))

        assert dto.task_id == 1
        assert dto.deadline is not None
        assert dto.name is None
        assert dto.priority is None

    @pytest.mark.parametrize("status", list(TaskStatus))
    def test_all_status_values_supported(self, status) -> None:
        """Test that all TaskStatus values can be used."""
        dto = UpdateTaskInput(task_id=1, status=status)
        assert dto.status == status
