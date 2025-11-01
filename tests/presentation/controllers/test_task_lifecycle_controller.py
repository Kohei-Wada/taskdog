"""Tests for TaskLifecycleController."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.controllers.task_lifecycle_controller import TaskLifecycleController


class TestTaskLifecycleController(unittest.TestCase):
    """Test cases for TaskLifecycleController."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=JsonTaskRepository)
        self.time_tracker = MagicMock()
        self.config = MagicMock()
        self.controller = TaskLifecycleController(
            repository=self.repository,
            time_tracker=self.time_tracker,
            config=self.config,
        )

    def test_start_task_returns_task_operation_output(self):
        """Test that start_task returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.start_task(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_complete_task_returns_task_operation_output(self):
        """Test that complete_task returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.complete_task(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_pause_task_returns_task_operation_output(self):
        """Test that pause_task returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.pause_task(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_cancel_task_returns_task_operation_output(self):
        """Test that cancel_task returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.cancel_task(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_reopen_task_returns_task_operation_output(self):
        """Test that reopen_task returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
            actual_end=datetime(2025, 1, 1, 17, 0, 0),
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.reopen_task(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_controller_has_time_tracker_dependency(self):
        """Test that controller has time_tracker attribute."""
        self.assertIsNotNone(self.controller.time_tracker)
        self.assertEqual(self.controller.time_tracker, self.time_tracker)

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        self.assertIsNotNone(self.controller.repository)
        self.assertIsNotNone(self.controller.config)
        self.assertEqual(self.controller.repository, self.repository)
        self.assertEqual(self.controller.config, self.config)


if __name__ == "__main__":
    unittest.main()
