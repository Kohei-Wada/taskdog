"""Tests for TaskService."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.config import TUIConfig
from presentation.tui.services.task_service import TaskService


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = MagicMock(spec=TaskRepository)
        self.time_tracker = MagicMock(spec=TimeTracker)
        self.query_service = MagicMock(spec=TaskQueryService)
        self.config = TUIConfig()
        self.service = TaskService(
            self.repository, self.time_tracker, self.query_service, self.config
        )

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

    def test_calculate_start_date_weekday(self):
        """Test start date calculation for weekdays."""
        # Mock datetime.now() to return a Monday
        with patch("presentation.tui.services.task_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 1, 6)  # Monday
            start_date = self.service._calculate_start_date()
            self.assertEqual(start_date.weekday(), 0)  # Monday

    def test_calculate_start_date_weekend(self):
        """Test start date calculation for weekends."""
        # Mock datetime.now() to return a Saturday
        with patch("presentation.tui.services.task_service.datetime") as mock_datetime:
            saturday = datetime(2025, 1, 4)  # Saturday
            mock_datetime.now.return_value = saturday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            start_date = self.service._calculate_start_date()
            # Should return next Monday
            self.assertEqual(start_date.weekday(), 0)  # Monday


if __name__ == "__main__":
    unittest.main()
