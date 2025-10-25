"""Tests for DependencyAwareOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestDependencyAwareOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for DependencyAwareOptimizationStrategy."""

    algorithm_name = "dependency_aware"

    def test_dependency_aware_sorts_by_deadline_then_priority(self):
        """Test that dependency-aware strategy sorts by deadline, then priority."""
        # Create tasks with different deadlines and priorities
        self.create_task(
            "High Priority, Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        self.create_task(
            "Low Priority, Early Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Early deadline task should be scheduled first
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        self.assertEqual(
            tasks_by_name["Low Priority, Early Deadline"].planned_start,
            datetime(2025, 10, 20, 9, 0, 0),
        )
        self.assertEqual(
            tasks_by_name["High Priority, Late Deadline"].planned_start,
            datetime(2025, 10, 21, 9, 0, 0),
        )

    def test_dependency_aware_uses_priority_as_tiebreaker(self):
        """Test that priority is used when deadlines are equal."""
        # Create tasks with same deadline but different priorities
        self.create_task(
            "Low Priority",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        self.create_task(
            "High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # High priority task should be scheduled first (same deadline)
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        self.assertEqual(
            tasks_by_name["High Priority"].planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        self.assertEqual(
            tasks_by_name["Low Priority"].planned_start, datetime(2025, 10, 21, 9, 0, 0)
        )

    def test_dependency_aware_schedules_no_deadline_tasks_last(self):
        """Test that tasks without deadlines are scheduled last."""
        # Create tasks with and without deadlines
        self.create_task(
            "With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        self.create_task("No Deadline", priority=100, estimated_duration=6.0, deadline=None)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task with deadline should be scheduled first
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        self.assertEqual(
            tasks_by_name["With Deadline"].planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        self.assertEqual(
            tasks_by_name["No Deadline"].planned_start, datetime(2025, 10, 21, 9, 0, 0)
        )

    def test_dependency_aware_uses_greedy_allocation(self):
        """Test that dependency-aware strategy uses greedy allocation."""
        # Create task that requires multiple days
        self.create_task(
            "Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        task = result.successful_tasks[0]

        # Verify greedy allocation: fills each day to maximum
        self.assertIsNotNone(task.daily_allocations)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 22), 0.0), 3.0, places=5)

    def test_dependency_aware_respects_deadlines(self):
        """Test that dependency-aware strategy respects deadlines."""
        # Create task with impossible deadline
        self.create_task(
            "Impossible Deadline",
            priority=100,
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Task should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_dependency_aware_handles_multiple_tasks(self):
        """Test that dependency-aware strategy handles multiple tasks correctly."""
        # Create multiple tasks with different characteristics
        self.create_task(
            "Urgent Low Priority",
            priority=30,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )
        self.create_task(
            "Medium Priority Medium Deadline",
            priority=60,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 23, 18, 0, 0),
        )
        self.create_task(
            "High Priority Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order (deadline first, then priority)
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # Earliest deadline should be first
        self.assertEqual(
            tasks_by_name["Urgent Low Priority"].planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        # Middle deadline should be second
        self.assertEqual(
            tasks_by_name["Medium Priority Medium Deadline"].planned_start,
            datetime(2025, 10, 21, 9, 0, 0),
        )
        # Latest deadline should be last
        self.assertEqual(
            tasks_by_name["High Priority Late Deadline"].planned_start,
            datetime(2025, 10, 22, 9, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
