"""Tests for TaskService."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.notes_repository import NotesRepository
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.context import TUIContext
from presentation.tui.services.task_service import TaskService
from shared.config_manager import ConfigManager


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = MagicMock(spec=TaskRepository)
        self.time_tracker = MagicMock(spec=TimeTracker)
        self.query_service = MagicMock(spec=TaskQueryService)
        self.notes_repository = MagicMock(spec=NotesRepository)
        self.config = ConfigManager._default_config()

        # Create TUIContext
        self.context = TUIContext(
            repository=self.repository,
            time_tracker=self.time_tracker,
            query_service=self.query_service,
            config=self.config,
            notes_repository=self.notes_repository,
        )

        # Initialize TaskService with context
        self.service = TaskService(self.context)

    def test_create_task_with_default_priority(self):
        """Test creating a task with default priority."""
        expected_task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            timestamp=datetime.now(),
        )

        with patch(
            "presentation.tui.services.task_service.CreateTaskUseCase"
        ) as mock_use_case_class:
            mock_use_case = MagicMock()
            mock_use_case.execute.return_value = expected_task
            mock_use_case_class.return_value = mock_use_case

            result = self.service.create_task("Test Task")

            self.assertEqual(result, expected_task)
            mock_use_case.execute.assert_called_once()

    def test_create_task_with_custom_priority(self):
        """Test creating a task with custom priority."""
        expected_task = Task(
            id=1,
            name="Test Task",
            priority=8,
            status=TaskStatus.PENDING,
            timestamp=datetime.now(),
        )

        with patch(
            "presentation.tui.services.task_service.CreateTaskUseCase"
        ) as mock_use_case_class:
            mock_use_case = MagicMock()
            mock_use_case.execute.return_value = expected_task
            mock_use_case_class.return_value = mock_use_case

            result = self.service.create_task("Test Task", priority=8)

            self.assertEqual(result, expected_task)

    def test_start_task(self):
        """Test starting a task."""
        task_id = 1
        expected_task = Task(
            id=task_id,
            name="Test Task",
            priority=5,
            status=TaskStatus.IN_PROGRESS,
            timestamp=datetime.now(),
        )

        with patch(
            "presentation.tui.services.task_service.StartTaskUseCase"
        ) as mock_use_case_class:
            mock_use_case = MagicMock()
            mock_use_case.execute.return_value = expected_task
            mock_use_case_class.return_value = mock_use_case

            result = self.service.start_task(task_id)

            self.assertEqual(result, expected_task)
            mock_use_case.execute.assert_called_once()

    def test_complete_task(self):
        """Test completing a task."""
        task_id = 1
        expected_task = Task(
            id=task_id,
            name="Test Task",
            priority=5,
            status=TaskStatus.COMPLETED,
            timestamp=datetime.now(),
        )

        with patch(
            "presentation.tui.services.task_service.CompleteTaskUseCase"
        ) as mock_use_case_class:
            mock_use_case = MagicMock()
            mock_use_case.execute.return_value = expected_task
            mock_use_case_class.return_value = mock_use_case

            result = self.service.complete_task(task_id)

            self.assertEqual(result, expected_task)
            mock_use_case.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
