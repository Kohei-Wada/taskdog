"""Tests for ArchiveTaskUseCase."""

import pytest

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.archive_task import ArchiveTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestArchiveTaskUseCase:
    """Test cases for ArchiveTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.use_case = ArchiveTaskUseCase(self.repository)

    def test_archive_completed_task(self):
        """Test archiving a completed task sets is_archived flag and preserves status."""
        # Create completed task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )

        # Archive task
        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived (is_archived=True, status preserved)
        assert result.is_archived is True
        assert result.status == TaskStatus.COMPLETED

        # Verify persisted
        archived_task = self.repository.get_by_id(task.id)
        assert archived_task is not None
        assert archived_task.is_archived is True
        assert archived_task.status == TaskStatus.COMPLETED

    def test_archive_canceled_task(self):
        """Test archiving a canceled task sets is_archived flag and preserves status."""
        # Create canceled task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.CANCELED
        )

        # Archive task
        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        assert result.is_archived is True
        assert result.status == TaskStatus.CANCELED

    def test_archive_pending_task(self):
        """Test archiving a pending task is allowed and preserves status."""
        # Create pending task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Archive task
        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        assert result.is_archived is True
        assert result.status == TaskStatus.PENDING

    def test_archive_in_progress_task(self):
        """Test archiving an in-progress task is allowed and preserves status."""
        # Create in-progress task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS
        )

        # Archive task
        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        assert result.is_archived is True
        assert result.status == TaskStatus.IN_PROGRESS

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = SingleTaskInput(task_id=999)

        with pytest.raises(TaskNotFoundException):
            self.use_case.execute(input_dto)
