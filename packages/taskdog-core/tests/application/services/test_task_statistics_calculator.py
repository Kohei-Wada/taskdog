"""Test cases for TaskStatisticsCalculator."""

import unittest
from datetime import datetime, timedelta

from taskdog_core.application.services.task_statistics_calculator import (
    TaskStatisticsCalculator,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskStatisticsCalculator(unittest.TestCase):
    """Test cases for TaskStatisticsCalculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TaskStatisticsCalculator()

    def test_calculate_task_statistics_empty(self):
        """Test basic statistics with empty task list."""
        result = self.calculator.calculate_all([])

        self.assertEqual(result.task_stats.total_tasks, 0)
        self.assertEqual(result.task_stats.pending_count, 0)
        self.assertEqual(result.task_stats.completed_count, 0)
        self.assertEqual(result.task_stats.completion_rate, 0.0)

    def test_calculate_task_statistics_basic(self):
        """Test basic task statistics."""
        tasks = [
            Task(name="Task 1", priority=10, id=1, status=TaskStatus.PENDING),
            Task(name="Task 2", priority=20, id=2, status=TaskStatus.IN_PROGRESS),
            Task(name="Task 3", priority=30, id=3, status=TaskStatus.COMPLETED),
            Task(name="Task 4", priority=40, id=4, status=TaskStatus.CANCELED),
            Task(name="Task 5", priority=50, id=5, status=TaskStatus.COMPLETED),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertEqual(result.task_stats.total_tasks, 5)
        self.assertEqual(result.task_stats.pending_count, 1)
        self.assertEqual(result.task_stats.in_progress_count, 1)
        self.assertEqual(result.task_stats.completed_count, 2)
        self.assertEqual(result.task_stats.canceled_count, 1)
        self.assertEqual(
            result.task_stats.completion_rate, 2.0 / 3.0
        )  # 2 completed / 3 finished

    def test_calculate_time_statistics(self):
        """Test time tracking statistics."""
        now = datetime.now()
        tasks = [
            Task(
                name="Task 1",
                priority=10,
                id=1,
                actual_start=(now - timedelta(hours=5)),
                actual_end=(now - timedelta(hours=3)),
            ),
            Task(
                name="Task 2",
                priority=20,
                id=2,
                actual_start=(now - timedelta(hours=10)),
                actual_end=(now - timedelta(hours=6)),
            ),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertIsNotNone(result.time_stats)
        self.assertEqual(result.time_stats.tasks_with_time_tracking, 2)
        self.assertEqual(result.time_stats.total_work_hours, 6.0)  # 2h + 4h
        self.assertEqual(result.time_stats.average_work_hours, 3.0)
        self.assertEqual(result.time_stats.median_work_hours, 3.0)
        self.assertIsNotNone(result.time_stats.longest_task)
        self.assertEqual(result.time_stats.longest_task.name, "Task 2")

    def test_calculate_estimation_accuracy(self):
        """Test estimation accuracy statistics."""
        now = datetime.now()
        tasks = [
            # Over-estimated (finished faster)
            Task(
                name="Task 1",
                priority=10,
                id=1,
                estimated_duration=10.0,
                actual_start=(now - timedelta(hours=5)),
                actual_end=now,
            ),
            # Under-estimated (took longer)
            Task(
                name="Task 2",
                priority=20,
                id=2,
                estimated_duration=2.0,
                actual_start=(now - timedelta(hours=5)),
                actual_end=now,
            ),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertIsNotNone(result.estimation_stats)
        self.assertEqual(result.estimation_stats.total_tasks_with_estimation, 2)
        self.assertEqual(result.estimation_stats.over_estimated_count, 1)
        self.assertEqual(result.estimation_stats.under_estimated_count, 1)

    def test_calculate_deadline_compliance(self):
        """Test deadline compliance statistics."""
        now = datetime.now()
        tasks = [
            # Met deadline
            Task(
                name="Task 1",
                priority=10,
                id=1,
                deadline=(now + timedelta(days=1)),
                actual_end=now,
                status=TaskStatus.COMPLETED,
            ),
            # Missed deadline
            Task(
                name="Task 2",
                priority=20,
                id=2,
                deadline=(now - timedelta(days=2)),
                actual_end=now,
                status=TaskStatus.COMPLETED,
            ),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertIsNotNone(result.deadline_stats)
        self.assertEqual(result.deadline_stats.total_tasks_with_deadline, 2)
        self.assertEqual(result.deadline_stats.met_deadline_count, 1)
        self.assertEqual(result.deadline_stats.missed_deadline_count, 1)
        self.assertEqual(result.deadline_stats.compliance_rate, 0.5)

    def test_calculate_priority_distribution(self):
        """Test priority distribution statistics."""
        tasks = [
            Task(name="High 1", priority=100, id=1, status=TaskStatus.COMPLETED),
            Task(name="High 2", priority=70, id=2, status=TaskStatus.PENDING),
            Task(name="Medium", priority=50, id=3, status=TaskStatus.COMPLETED),
            Task(name="Low", priority=10, id=4, status=TaskStatus.COMPLETED),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertEqual(result.priority_stats.high_priority_count, 2)
        self.assertEqual(result.priority_stats.medium_priority_count, 1)
        self.assertEqual(result.priority_stats.low_priority_count, 1)
        self.assertEqual(result.priority_stats.high_priority_completion_rate, 0.5)

    def test_calculate_trends(self):
        """Test trend statistics."""
        now = datetime.now()
        tasks = [
            # Completed 5 days ago
            Task(
                name="Task 1",
                priority=10,
                id=1,
                actual_end=(now - timedelta(days=5)),
                status=TaskStatus.COMPLETED,
            ),
            # Completed 20 days ago
            Task(
                name="Task 2",
                priority=20,
                id=2,
                actual_end=(now - timedelta(days=20)),
                status=TaskStatus.COMPLETED,
            ),
        ]

        result = self.calculator.calculate_all(tasks)

        self.assertIsNotNone(result.trend_stats)
        self.assertEqual(result.trend_stats.last_7_days_completed, 1)
        self.assertEqual(result.trend_stats.last_30_days_completed, 2)

    def test_filter_by_period_7d(self):
        """Test filtering tasks by 7-day period."""
        now = datetime.now()
        tasks = [
            # Completed 5 days ago (should be included)
            Task(
                name="Task 1",
                priority=10,
                id=1,
                actual_end=(now - timedelta(days=5)),
                status=TaskStatus.COMPLETED,
            ),
            # Completed 10 days ago (should be excluded)
            Task(
                name="Task 2",
                priority=20,
                id=2,
                actual_end=(now - timedelta(days=10)),
                status=TaskStatus.COMPLETED,
            ),
        ]

        result = self.calculator.calculate_all(tasks, period="7d")

        self.assertEqual(result.task_stats.total_tasks, 1)
        self.assertEqual(result.task_stats.completed_count, 1)


if __name__ == "__main__":
    unittest.main()
