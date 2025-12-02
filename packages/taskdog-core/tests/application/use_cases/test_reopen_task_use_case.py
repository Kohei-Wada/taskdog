"""Tests for ReopenTaskUseCase."""

from datetime import datetime

import pytest

from taskdog_core.application.dto.single_task_inputs import ReopenTaskInput
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestReopenTaskUseCase:
    """Test cases for ReopenTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = ReopenTaskUseCase(self.repository)

    @pytest.mark.parametrize(
        "status,has_actual_start,has_actual_end",
        [
            (TaskStatus.COMPLETED, True, True),
            (TaskStatus.CANCELED, False, True),
        ],
        ids=["completed_task", "canceled_task"],
    )
    def test_execute_reopens_finished_tasks(
        self, status, has_actual_start, has_actual_end
    ):
        """Test execute reopens completed/canceled tasks."""
        create_kwargs = {
            "name": "Test Task",
            "priority": 1,
            "status": status,
        }
        if has_actual_start:
            create_kwargs["actual_start"] = datetime(2025, 1, 1, 9, 0, 0)
        if has_actual_end:
            create_kwargs["actual_end"] = datetime(2025, 1, 1, 12, 0, 0)

        task = self.repository.create(**create_kwargs)

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.status == TaskStatus.PENDING
        assert result.actual_start is None
        assert result.actual_end is None

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
            actual_end=datetime(2025, 1, 1, 12, 0, 0),
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.status == TaskStatus.PENDING
        assert retrieved.actual_start is None
        assert retrieved.actual_end is None

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = ReopenTaskInput(task_id=999)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    @pytest.mark.parametrize(
        "status,expected_message",
        [
            (TaskStatus.PENDING, "Cannot reopen task with status PENDING"),
            (TaskStatus.IN_PROGRESS, "Cannot reopen task with status IN_PROGRESS"),
        ],
        ids=["pending_task", "in_progress_task"],
    )
    def test_execute_with_unfinished_task_raises_error(self, status, expected_message):
        """Test execute with PENDING/IN_PROGRESS task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=status)

        input_dto = ReopenTaskInput(task_id=task.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert expected_message in str(exc_info.value)

    def test_execute_with_dependencies_always_succeeds(self):
        """Test that reopen succeeds regardless of dependency states.

        Dependencies are NOT validated during reopen. This allows flexible
        restoration of task states. Dependency validation will occur when
        attempting to start the task.
        """
        # Create dependency (not completed)
        dep = self.repository.create(
            name="Dependency", priority=1, status=TaskStatus.PENDING
        )

        # Create completed task depending on pending task
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep.id],
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency is not completed
        assert result.status == TaskStatus.PENDING

    def test_execute_with_missing_dependency_succeeds(self):
        """Test that reopen succeeds even with missing dependencies."""
        # Create completed task with non-existent dependency
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[999],  # Non-existent task
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency doesn't exist
        assert result.status == TaskStatus.PENDING

    def test_execute_with_no_dependencies_succeeds(self):
        """Test execute with no dependencies succeeds."""
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.status == TaskStatus.PENDING
