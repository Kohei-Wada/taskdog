"""Tests for RemoveTaskUseCase."""

from unittest.mock import MagicMock

import pytest

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.remove_task import RemoveTaskUseCase
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestRemoveTaskUseCase:
    """Test cases for RemoveTaskUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.notes_repository = MagicMock()
        self.use_case = RemoveTaskUseCase(self.repository, self.notes_repository)

    def test_remove_task(self):
        """Test removing a task."""
        # Create task
        task = self.repository.create(name="Test Task", priority=1)

        # Remove task
        input_dto = SingleTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task removed
        assert self.repository.get_by_id(task.id) is None

        # Verify notes deletion was called
        self.notes_repository.delete_notes.assert_called_once_with(task.id)

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        input_dto = SingleTaskInput(task_id=999)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999
