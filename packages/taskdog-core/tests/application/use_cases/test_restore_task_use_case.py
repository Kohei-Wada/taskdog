"""Tests for RestoreTaskUseCase."""

import pytest

from taskdog_core.application.dto.single_task_inputs import RestoreTaskInput
from taskdog_core.application.use_cases.restore_task import RestoreTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestRestoreTaskUseCase:
    """Test cases for RestoreTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = RestoreTaskUseCase(self.repository)

    def test_execute_restores_archived_task(self):
        """Test execute clears is_archived flag and preserves status."""
        # Create an archived task (PENDING + is_archived)
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        assert result.is_archived is False
        assert result.status == TaskStatus.PENDING

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        # Create an archived task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved.is_archived is False
        assert retrieved.status == TaskStatus.PENDING

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = RestoreTaskInput(task_id=999)

        with pytest.raises(TaskNotFoundException):
            self.use_case.execute(input_dto)

    def test_execute_cannot_restore_non_archived_task(self):
        """Test execute with non-archived task raises ValidationError."""
        # Create a completed (but not archived) task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )

        input_dto = RestoreTaskInput(task_id=task.id)

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "Only archived" in str(exc_info.value)

    def test_execute_preserves_other_fields(self):
        """Test execute only modifies is_archived flag."""
        # Create archived task with various fields
        task = self.repository.create(
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
        )
        task.is_archived = True
        self.repository.save(task)

        original_name = task.name
        original_priority = task.priority
        original_duration = task.estimated_duration
        original_status = task.status

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify only is_archived changed
        assert result.is_archived is False
        assert result.status == original_status
        assert result.name == original_name
        assert result.priority == original_priority
        assert result.estimated_duration == original_duration

    def test_execute_restores_archived_completed_task(self):
        """Test execute restores archived COMPLETED task with original status."""
        # Create an archived completed task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify archived flag cleared and status preserved
        assert result.is_archived is False
        assert result.status == TaskStatus.COMPLETED

    def test_execute_restores_archived_canceled_task(self):
        """Test execute restores archived CANCELED task with original status."""
        # Create an archived canceled task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.CANCELED
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify archived flag cleared and status preserved
        assert result.is_archived is False
        assert result.status == TaskStatus.CANCELED
