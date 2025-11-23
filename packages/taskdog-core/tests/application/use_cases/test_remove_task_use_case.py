import unittest
"""Tests for RemoveTaskUseCase."""

from unittest.mock import MagicMock

from taskdog_core.application.dto.remove_task_input import RemoveTaskInput
from taskdog_core.application.use_cases.remove_task import RemoveTaskUseCase
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from tests.test_fixtures import InMemoryDatabaseTestCase


class RemoveTaskUseCaseTest(InMemoryDatabaseTestCase):
    """Test cases for RemoveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.notes_repository = MagicMock()
        self.use_case = RemoveTaskUseCase(self.repository, self.notes_repository)

    def test_remove_task(self):
        """Test removing a task."""
        # Create task
        task = self.repository.create(name="Test Task", priority=1)

        # Remove task
        input_dto = RemoveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task removed
        self.assertIsNone(self.repository.get_by_id(task.id))

        # Verify notes deletion was called
        self.notes_repository.delete_notes.assert_called_once_with(task.id)

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        input_dto = RemoveTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)


if __name__ == "__main__":
    unittest.main()
