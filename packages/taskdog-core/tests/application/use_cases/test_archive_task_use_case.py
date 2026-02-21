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

    @pytest.mark.parametrize(
        "status",
        [
            TaskStatus.COMPLETED,
            TaskStatus.CANCELED,
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
        ],
        ids=["completed", "canceled", "pending", "in_progress"],
    )
    def test_archive_preserves_status(self, status):
        """Test archiving a task sets is_archived flag and preserves status."""
        task = self.repository.create(name="Test Task", priority=1, status=status)
        input_dto = SingleTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)
        assert result.is_archived is True
        assert result.status == status
        archived_task = self.repository.get_by_id(task.id)
        assert archived_task.is_archived is True
        assert archived_task.status == status

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = SingleTaskInput(task_id=999)

        with pytest.raises(TaskNotFoundException):
            self.use_case.execute(input_dto)
