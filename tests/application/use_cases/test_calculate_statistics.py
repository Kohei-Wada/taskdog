"""Test cases for CalculateStatisticsUseCase."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from application.dto.statistics_result import CalculateStatisticsRequest
from application.use_cases.calculate_statistics import CalculateStatisticsUseCase
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task, TaskStatus


class TestCalculateStatisticsUseCase(unittest.TestCase):
    """Test cases for CalculateStatisticsUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = Mock()
        self.use_case = CalculateStatisticsUseCase(self.repository)

    def test_execute_with_empty_tasks(self):
        """Test execute with empty task list."""
        self.repository.get_all.return_value = []

        result = self.use_case.execute(CalculateStatisticsRequest())

        self.assertEqual(result.task_stats.total_tasks, 0)
        self.repository.get_all.assert_called_once()

    def test_execute_with_basic_tasks(self):
        """Test execute with basic tasks."""
        tasks = [
            Task(name="Task 1", priority=10, id=1, status=TaskStatus.PENDING),
            Task(name="Task 2", priority=20, id=2, status=TaskStatus.COMPLETED),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsRequest())

        self.assertEqual(result.task_stats.total_tasks, 2)
        self.assertEqual(result.task_stats.pending_count, 1)
        self.assertEqual(result.task_stats.completed_count, 1)
        self.repository.get_all.assert_called_once()

    def test_execute_with_period_filter(self):
        """Test execute with period filter."""
        now = datetime.now()
        tasks = [
            Task(
                name="Recent",
                priority=10,
                id=1,
                actual_end=(now - timedelta(days=3)).strftime(DATETIME_FORMAT),
                status=TaskStatus.COMPLETED,
            ),
            Task(
                name="Old",
                priority=20,
                id=2,
                actual_end=(now - timedelta(days=10)).strftime(DATETIME_FORMAT),
                status=TaskStatus.COMPLETED,
            ),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsRequest(period="7d"))

        # Only the recent task should be counted
        self.assertEqual(result.task_stats.total_tasks, 1)
        self.assertEqual(result.task_stats.completed_count, 1)
        self.repository.get_all.assert_called_once()

    def test_execute_calculates_all_statistics(self):
        """Test that execute calculates all statistics sections."""
        now = datetime.now()
        tasks = [
            Task(
                name="Task 1",
                priority=100,
                id=1,
                status=TaskStatus.COMPLETED,
                estimated_duration=5.0,
                deadline=(now + timedelta(days=1)).strftime(DATETIME_FORMAT),
                actual_start=(now - timedelta(hours=3)).strftime(DATETIME_FORMAT),
                actual_end=now.strftime(DATETIME_FORMAT),
            ),
        ]
        self.repository.get_all.return_value = tasks

        result = self.use_case.execute(CalculateStatisticsRequest())

        # Verify all statistics sections are calculated
        self.assertIsNotNone(result.task_stats)
        self.assertIsNotNone(result.time_stats)
        self.assertIsNotNone(result.estimation_stats)
        self.assertIsNotNone(result.deadline_stats)
        self.assertIsNotNone(result.priority_stats)
        self.assertIsNotNone(result.trend_stats)


if __name__ == "__main__":
    unittest.main()
