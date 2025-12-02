"""Base test class for status change use cases.

This module provides a base test class that consolidates common test patterns
across StartTaskUseCase, CompleteTaskUseCase, PauseTaskUseCase, and CancelTaskUseCase.
"""

import contextlib
from datetime import datetime

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)


class BaseStatusChangeUseCaseTest:
    """Base test class for status change use cases.

    Subclasses must override:
    - use_case_class: The use case class to test
    - request_class: The request DTO class
    - target_status: The expected status after execution
    - initial_status: The initial task status (default: PENDING)
    - sets_actual_start: Whether the use case sets actual_start (default: False)
    - sets_actual_end: Whether the use case sets actual_end (default: False)
    - clears_actual_start: Whether the use case clears actual_start (default: False)
    - clears_actual_end: Whether the use case clears actual_end (default: False)
    """

    # Override in subclasses
    use_case_class = None
    request_class = None
    target_status = None
    initial_status = TaskStatus.PENDING

    # Timestamp behavior flags
    sets_actual_start = False
    sets_actual_end = False
    clears_actual_start = False
    clears_actual_end = False

    # Additional error tests
    test_not_started_error = False  # Only for CompleteTaskUseCase

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = self.use_case_class(self.repository)

    def test_execute_sets_correct_status(self):
        """Test execute sets task status to the target status."""
        task = Task(name="Test Task", priority=1, status=self.initial_status)
        task.id = self.repository.generate_next_id()
        if self.initial_status == TaskStatus.IN_PROGRESS:
            task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = self.request_class(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.status == self.target_status

    def test_execute_handles_timestamps_correctly(self):
        """Test execute handles actual_start/actual_end timestamps correctly."""
        task = Task(name="Test Task", priority=1, status=self.initial_status)
        task.id = self.repository.generate_next_id()
        if self.initial_status == TaskStatus.IN_PROGRESS:
            task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = self.request_class(task_id=task.id)
        result = self.use_case.execute(input_dto)

        if self.sets_actual_start:
            assert result.actual_start is not None
        if self.sets_actual_end:
            assert result.actual_end is not None
        if self.clears_actual_start:
            assert result.actual_start is None
        if self.clears_actual_end:
            assert result.actual_end is None

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = Task(name="Test Task", priority=1, status=self.initial_status)
        task.id = self.repository.generate_next_id()
        if self.initial_status == TaskStatus.IN_PROGRESS:
            task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = self.request_class(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.status == self.target_status

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = self.request_class(task_id=999)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    @pytest.mark.parametrize(
        "finished_status,description",
        [
            (TaskStatus.COMPLETED, "COMPLETED task"),
            (TaskStatus.CANCELED, "CANCELED task"),
        ],
        ids=["completed_task", "canceled_task"],
    )
    def test_execute_raises_error_for_finished_tasks(
        self, finished_status, description
    ):
        """Test execute raises TaskAlreadyFinishedError for finished tasks."""
        task = Task(name="Test Task", priority=1, status=finished_status)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(2024, 1, 1, 12, 0, 0)
        self.repository.save(task)

        input_dto = self.request_class(task_id=task.id)

        with pytest.raises(TaskAlreadyFinishedError) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == task.id
        assert exc_info.value.status == finished_status.value

    def test_execute_does_not_modify_finished_task_state(self):
        """Test execute does not modify state when attempted on finished task."""
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(2024, 1, 1, 12, 0, 0)
        self.repository.save(task)

        input_dto = self.request_class(task_id=task.id)

        with contextlib.suppress(TaskAlreadyFinishedError):
            self.use_case.execute(input_dto)

        # Verify task state remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.status == TaskStatus.COMPLETED
        assert retrieved.actual_start == datetime(2024, 1, 1, 10, 0, 0)
        assert retrieved.actual_end == datetime(2024, 1, 1, 12, 0, 0)
