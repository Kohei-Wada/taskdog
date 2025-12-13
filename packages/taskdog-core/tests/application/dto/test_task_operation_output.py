"""Tests for TaskOperationOutput DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskOperationOutput:
    """Test suite for TaskOperationOutput DTO."""

    def test_create_with_all_fields(self) -> None:
        """Test creating DTO with all fields populated."""
        dto = TaskOperationOutput(
            id=1,
            name="Test Task",
            status=TaskStatus.IN_PROGRESS,
            priority=2,
            deadline=datetime(2025, 1, 10, 23, 59),
            estimated_duration=10.5,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=None,
            depends_on=[2, 3],
            tags=["urgent", "backend"],
            is_fixed=True,
            is_archived=False,
            actual_duration_hours=5.5,
            daily_allocations={"2025-01-01": 4.0},
        )

        assert dto.id == 1
        assert dto.name == "Test Task"
        assert dto.status == TaskStatus.IN_PROGRESS
        assert dto.priority == 2
        assert dto.deadline is not None
        assert dto.estimated_duration == 10.5
        assert dto.is_fixed is True
        assert dto.is_archived is False
        assert len(dto.depends_on) == 2
        assert len(dto.tags) == 2

    def test_create_with_minimal_fields(self) -> None:
        """Test creating DTO with minimal required fields."""
        dto = TaskOperationOutput(
            id=1,
            name="Minimal Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )

        assert dto.id == 1
        assert dto.name == "Minimal Task"
        assert dto.deadline is None
        assert dto.depends_on == []
        assert dto.tags == []

    def test_from_task_converts_task_entity(self) -> None:
        """Test from_task factory method converts Task entity."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        dto = TaskOperationOutput.from_task(task)

        assert dto.id == task.id
        assert dto.name == task.name
        assert dto.status == task.status
        assert dto.priority == task.priority

    def test_from_task_raises_error_when_task_id_is_none(self) -> None:
        """Test from_task raises ValueError when task.id is None."""
        task = Task(
            id=None,
            name="Task without ID",
            priority=1,
        )

        with pytest.raises(ValueError) as exc_info:
            TaskOperationOutput.from_task(task)

        assert "Cannot convert task without ID" in str(exc_info.value)

    def test_from_task_preserves_all_task_fields(self) -> None:
        """Test from_task preserves all Task entity fields."""
        task = Task(
            id=123,
            name="Complete Task",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 18, 0),
            deadline=datetime(2025, 1, 10, 23, 59),
            actual_start=datetime(2025, 1, 1, 9, 30),
            actual_end=datetime(2025, 1, 5, 17, 45),
            estimated_duration=20.5,
            is_fixed=True,
            depends_on=[1, 2, 3],
            tags=["urgent", "backend", "refactoring"],
            is_archived=False,
        )

        dto = TaskOperationOutput.from_task(task)

        assert dto.id == task.id
        assert dto.name == task.name
        assert dto.priority == task.priority
        assert dto.status == task.status
        assert dto.planned_start == task.planned_start
        assert dto.planned_end == task.planned_end
        assert dto.deadline == task.deadline
        assert dto.actual_start == task.actual_start
        assert dto.actual_end == task.actual_end
        assert dto.estimated_duration == task.estimated_duration
        assert dto.is_fixed == task.is_fixed
        assert dto.depends_on == task.depends_on
        assert dto.tags == task.tags
        assert dto.is_archived == task.is_archived

    def test_equality(self) -> None:
        """Test equality comparison."""
        dto1 = TaskOperationOutput(
            id=1,
            name="Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )
        dto2 = TaskOperationOutput(
            id=1,
            name="Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )

        assert dto1 == dto2

    def test_repr_includes_id_and_name(self) -> None:
        """Test that repr includes id and name."""
        dto = TaskOperationOutput(
            id=42,
            name="Test Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )
        repr_str = repr(dto)

        assert "id=42" in repr_str
        assert "Test Task" in repr_str

    def test_from_task_with_completed_task(self) -> None:
        """Test from_task with a completed task that has actual_duration_hours."""
        task = Task(
            id=1,
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0),
            actual_end=datetime(2025, 1, 1, 17, 0),
        )

        dto = TaskOperationOutput.from_task(task)

        assert dto.status == TaskStatus.COMPLETED
        assert dto.actual_end is not None
        # actual_duration_hours is computed property
        assert dto.actual_duration_hours is not None

    def test_from_task_with_archived_task(self) -> None:
        """Test from_task preserves is_archived flag."""
        task = Task(
            id=1,
            name="Archived Task",
            priority=1,
            is_archived=True,
        )

        dto = TaskOperationOutput.from_task(task)

        assert dto.is_archived is True
