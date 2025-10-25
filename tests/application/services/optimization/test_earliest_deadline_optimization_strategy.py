"""Tests for EarliestDeadlineOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestEarliestDeadlineOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for EarliestDeadlineOptimizationStrategy."""

    algorithm_name = "earliest_deadline"

    def test_earliest_deadline_schedules_by_deadline_order(self):
        """Test that EDF schedules tasks by deadline, not priority."""
        # Create two tasks with opposite priority/deadline relationship
        # Task 1: Low priority, early deadline (should be scheduled first)
        self.create_task(
            "Early Deadline Task",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )
        # Task 2: High priority, late deadline (should be scheduled second)
        self.create_task(
            "Late Deadline Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task 1 (early deadline) should start first
        task1 = next(t for t in result.successful_tasks if t.name == "Early Deadline Task")
        task2 = next(t for t in result.successful_tasks if t.name == "Late Deadline Task")

        self.assertEqual(task1.planned_start, datetime(2025, 10, 20, 9, 0, 0))  # Monday
        self.assertEqual(task2.planned_start, datetime(2025, 10, 21, 9, 0, 0))  # Tuesday

    def test_earliest_deadline_handles_no_deadline(self):
        """Test that EDF schedules tasks without deadlines last."""
        # Task 1: Has deadline (should be scheduled first)
        self.create_task(
            "With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        # Task 2: No deadline (should be scheduled last)
        self.create_task("No Deadline", priority=100, estimated_duration=6.0, deadline=None)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task with deadline should start first
        task1 = next(t for t in result.successful_tasks if t.name == "With Deadline")
        task2 = next(t for t in result.successful_tasks if t.name == "No Deadline")

        self.assertEqual(task1.planned_start, datetime(2025, 10, 20, 9, 0, 0))  # Monday
        self.assertEqual(task2.planned_start, datetime(2025, 10, 21, 9, 0, 0))  # Tuesday

    def test_earliest_deadline_respects_deadline_constraints(self):
        """Test that EDF fails tasks that cannot meet their deadlines."""
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

    def test_earliest_deadline_ignores_priority_completely(self):
        """Test that EDF ignores priority field when scheduling."""
        # Create three tasks with different priorities and deadlines
        # Priority should have NO effect on scheduling order
        self.create_task(
            "Highest Priority, Latest Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )
        self.create_task(
            "Medium Priority, Middle Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )
        self.create_task(
            "Lowest Priority, Earliest Deadline",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order matches deadline order, not priority
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # Earliest deadline should be scheduled first
        self.assertEqual(
            tasks_by_name["Lowest Priority, Earliest Deadline"].planned_start,
            datetime(2025, 10, 20, 9, 0, 0),
        )
        # Middle deadline should be scheduled second
        self.assertEqual(
            tasks_by_name["Medium Priority, Middle Deadline"].planned_start,
            datetime(2025, 10, 21, 9, 0, 0),
        )
        # Latest deadline should be scheduled last
        self.assertEqual(
            tasks_by_name["Highest Priority, Latest Deadline"].planned_start,
            datetime(2025, 10, 22, 9, 0, 0),
        )

    def test_earliest_deadline_uses_greedy_allocation(self):
        """Test that EDF uses greedy forward allocation strategy."""
        # Create task that requires multiple days
        self.create_task(
            "Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        task = result.successful_tasks[0]

        # Verify greedy allocation: fills each day to maximum before moving to next
        self.assertIsNotNone(task.daily_allocations)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 22), 0.0), 3.0, places=5)


if __name__ == "__main__":
    unittest.main()
