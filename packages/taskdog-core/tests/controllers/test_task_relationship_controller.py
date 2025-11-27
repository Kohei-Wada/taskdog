"""Tests for TaskRelationshipController."""

import unittest
from unittest.mock import MagicMock, Mock

from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.logger import Logger
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskRelationshipController(unittest.TestCase):
    """Test cases for TaskRelationshipController."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.config = MagicMock()
        self.logger = Mock(spec=Logger)
        self.controller = TaskRelationshipController(
            repository=self.repository,
            config=self.config,
            logger=self.logger,
        )

    def test_add_dependency_returns_task_operation_output(self):
        """Test that add_dependency returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        depends_on_id = 2
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[],
        )
        dependency_task = Task(
            id=depends_on_id,
            name="Dependency Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        # Return appropriate task based on ID (cycle detection calls get_by_id multiple times)
        def get_by_id_side_effect(task_id_arg):
            if task_id_arg == task_id:
                return task
            elif task_id_arg == depends_on_id:
                return dependency_task
            return None

        self.repository.get_by_id.side_effect = get_by_id_side_effect
        self.repository.save.return_value = None

        # Act
        result = self.controller.add_dependency(task_id, depends_on_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)

    def test_remove_dependency_returns_task_operation_output(self):
        """Test that remove_dependency returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        depends_on_id = 2
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[depends_on_id],
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.remove_dependency(task_id, depends_on_id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)

    def test_set_task_tags_returns_task_operation_output(self):
        """Test that set_task_tags returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        tags = ["work", "urgent"]
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=[],
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.set_task_tags(task_id, tags)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)

    def test_log_hours_returns_task_operation_output(self):
        """Test that log_hours returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        hours = 2.5
        date = "2025-01-15"
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.log_hours(task_id, hours, date)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task_id)

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        self.assertIsNotNone(self.controller.repository)
        self.assertIsNotNone(self.controller.config)
        self.assertEqual(self.controller.repository, self.repository)
        self.assertEqual(self.controller.config, self.config)


if __name__ == "__main__":
    unittest.main()
