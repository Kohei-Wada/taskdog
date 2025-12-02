"""Tests for TaskListOutput DTO."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus


@pytest.fixture
def task1():
    """Create first sample task."""
    now = datetime.now()
    return TaskRowDto(
        id=1,
        name="Task 1",
        priority=1,
        status=TaskStatus.PENDING,
        is_fixed=False,
        depends_on=[],
        tags=[],
        estimated_duration=None,
        actual_duration_hours=None,
        planned_start=None,
        planned_end=None,
        actual_start=None,
        actual_end=None,
        deadline=None,
        created_at=now,
        updated_at=now,
        is_archived=False,
        is_finished=False,
    )


@pytest.fixture
def task2():
    """Create second sample task."""
    now = datetime.now()
    return TaskRowDto(
        id=2,
        name="Task 2",
        priority=2,
        status=TaskStatus.IN_PROGRESS,
        is_fixed=False,
        depends_on=[],
        tags=["urgent"],
        estimated_duration=5.0,
        actual_duration_hours=None,
        planned_start=None,
        planned_end=None,
        actual_start=now,
        actual_end=None,
        deadline=None,
        created_at=now,
        updated_at=now,
        is_archived=False,
        is_finished=False,
    )


class TestTaskListOutput:
    """Test suite for TaskListOutput DTO."""

    def test_create_with_empty_task_list(self) -> None:
        """Test creating DTO with empty task list."""
        dto = TaskListOutput(tasks=[], total_count=0, filtered_count=0)

        assert dto.tasks == []
        assert dto.total_count == 0
        assert dto.filtered_count == 0

    def test_create_with_tasks(self, task1, task2) -> None:
        """Test creating DTO with tasks."""
        dto = TaskListOutput(
            tasks=[task1, task2],
            total_count=10,
            filtered_count=2,
        )

        assert len(dto.tasks) == 2
        assert dto.tasks[0] == task1
        assert dto.tasks[1] == task2
        assert dto.total_count == 10
        assert dto.filtered_count == 2

    def test_total_count_greater_than_filtered_count(self, task1) -> None:
        """Test when total_count is greater than filtered_count (filtering applied)."""
        dto = TaskListOutput(
            tasks=[task1],
            total_count=100,
            filtered_count=1,
        )

        assert dto.total_count > dto.filtered_count
        assert len(dto.tasks) == dto.filtered_count

    def test_total_count_equals_filtered_count(self, task1, task2) -> None:
        """Test when total_count equals filtered_count (no filtering)."""
        dto = TaskListOutput(
            tasks=[task1, task2],
            total_count=2,
            filtered_count=2,
        )

        assert dto.total_count == dto.filtered_count
        assert len(dto.tasks) == 2

    def test_equality(self, task1) -> None:
        """Test equality comparison."""
        dto1 = TaskListOutput(tasks=[task1], total_count=1, filtered_count=1)
        dto2 = TaskListOutput(tasks=[task1], total_count=1, filtered_count=1)

        assert dto1 == dto2

    def test_inequality_with_different_counts(self, task1) -> None:
        """Test inequality when counts differ."""
        dto1 = TaskListOutput(tasks=[task1], total_count=10, filtered_count=1)
        dto2 = TaskListOutput(tasks=[task1], total_count=5, filtered_count=1)

        assert dto1 != dto2

    def test_tasks_list_is_immutable_reference(self, task1, task2) -> None:
        """Test that tasks list reference is preserved."""
        tasks = [task1, task2]
        dto = TaskListOutput(tasks=tasks, total_count=2, filtered_count=2)

        assert dto.tasks is tasks

    def test_repr_includes_counts(self) -> None:
        """Test that repr includes count information."""
        dto = TaskListOutput(tasks=[], total_count=100, filtered_count=50)
        repr_str = repr(dto)

        assert "total_count=100" in repr_str
        assert "filtered_count=50" in repr_str

    def test_create_with_single_task(self, task1) -> None:
        """Test creating DTO with single task."""
        dto = TaskListOutput(tasks=[task1], total_count=1, filtered_count=1)

        assert len(dto.tasks) == 1
        assert dto.tasks[0] == task1

    def test_filtered_count_can_be_zero_with_nonzero_total(self) -> None:
        """Test filtered_count of zero with non-zero total_count."""
        dto = TaskListOutput(tasks=[], total_count=50, filtered_count=0)

        assert len(dto.tasks) == 0
        assert dto.total_count == 50
        assert dto.filtered_count == 0
