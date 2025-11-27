"""Tests for TaskLifecycleController."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock

from parameterized import parameterized

from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.logger import Logger
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskLifecycleController(unittest.TestCase):
    """Test cases for TaskLifecycleController."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.config = MagicMock()
        self.logger = Mock(spec=Logger)
        self.controller = TaskLifecycleController(
            repository=self.repository,
            config=self.config,
            logger=self.logger,
        )

    @parameterized.expand(
        [
            (
                "start_task",
                "start_task",
                TaskStatus.PENDING,
                None,
                None,
            ),
            (
                "complete_task",
                "complete_task",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "pause_task",
                "pause_task",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "cancel_task",
                "cancel_task",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "reopen_task",
                "reopen_task",
                TaskStatus.COMPLETED,
                datetime(2025, 1, 1, 9, 0, 0),
                datetime(2025, 1, 1, 17, 0, 0),
            ),
        ]
    )
    def test_lifecycle_operation_returns_task_operation_output(
        self, operation_name, method_name, initial_status, actual_start, actual_end
    ):
        """Test that lifecycle operations return TaskOperationOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=initial_status,
            actual_start=actual_start,
            actual_end=actual_end,
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        method = getattr(self.controller, method_name)
        result = method(task_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)
        self.assertEqual(result.name, "Test Task")

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        self.assertIsNotNone(self.controller.repository)
        self.assertIsNotNone(self.controller.config)
        self.assertEqual(self.controller.repository, self.repository)
        self.assertEqual(self.controller.config, self.config)


if __name__ == "__main__":
    unittest.main()
