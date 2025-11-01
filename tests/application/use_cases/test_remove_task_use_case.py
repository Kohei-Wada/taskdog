"""Tests for RemoveTaskUseCase."""

import tempfile
import unittest

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class RemoveTaskUseCaseTest(unittest.TestCase):
    """Test cases for RemoveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.use_case = RemoveTaskUseCase(self.repository)

    def test_remove_task(self):
        """Test removing a task."""
        # Create task
        task = self.repository.create(name="Test Task", priority=1)

        # Remove task
        input_dto = RemoveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task removed
        self.assertIsNone(self.repository.get_by_id(task.id))

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        input_dto = RemoveTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)


if __name__ == "__main__":
    unittest.main()
