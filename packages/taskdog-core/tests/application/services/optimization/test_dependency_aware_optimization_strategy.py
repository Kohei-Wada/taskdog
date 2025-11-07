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
        high_late = self.create_task(
            "High Priority, Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        low_early = self.create_task(
            "Low Priority, Early Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Early deadline task should be scheduled first
        updated_low_early = self.repository.get_by_id(low_early.id)
        updated_high_late = self.repository.get_by_id(high_late.id)
        assert updated_low_early is not None and updated_high_late is not None

        self.assertEqual(
            updated_low_early.planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        self.assertEqual(
            updated_high_late.planned_start, datetime(2025, 10, 21, 9, 0, 0)
        )

    def test_dependency_aware_uses_priority_as_tiebreaker(self):
        """Test that priority is used when deadlines are equal."""
        # Create tasks with same deadline but different priorities
        low_priority = self.create_task(
            "Low Priority",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        high_priority = self.create_task(
            "High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # High priority task should be scheduled first (same deadline)
        updated_high = self.repository.get_by_id(high_priority.id)
        updated_low = self.repository.get_by_id(low_priority.id)
        assert updated_high is not None and updated_low is not None

        self.assertEqual(updated_high.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        self.assertEqual(updated_low.planned_start, datetime(2025, 10, 21, 9, 0, 0))

    def test_dependency_aware_schedules_no_deadline_tasks_last(self):
        """Test that tasks without deadlines are scheduled last."""
        # Create tasks with and without deadlines
        with_deadline = self.create_task(
            "With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        no_deadline = self.create_task(
            "No Deadline", priority=100, estimated_duration=6.0, deadline=None
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task with deadline should be scheduled first
        updated_with = self.repository.get_by_id(with_deadline.id)
        updated_no = self.repository.get_by_id(no_deadline.id)
        assert updated_with is not None and updated_no is not None

        self.assertEqual(updated_with.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        self.assertEqual(updated_no.planned_start, datetime(2025, 10, 21, 9, 0, 0))

    def test_dependency_aware_uses_greedy_allocation(self):
        """Test that dependency-aware strategy uses greedy allocation."""
        # Create task that requires multiple days
        task = self.create_task(
            "Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Refetch task from repository to get updated state
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None

        # Verify greedy allocation: fills each day to maximum
        self.assertIsNotNone(updated_task.daily_allocations)
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5
        )
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5
        )
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 22), 0.0), 3.0, places=5
        )

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
        urgent_low = self.create_task(
            "Urgent Low Priority",
            priority=30,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )
        medium_medium = self.create_task(
            "Medium Priority Medium Deadline",
            priority=60,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 23, 18, 0, 0),
        )
        high_late = self.create_task(
            "High Priority Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order (deadline first, then priority)
        updated_urgent = self.repository.get_by_id(urgent_low.id)
        updated_medium = self.repository.get_by_id(medium_medium.id)
        updated_high = self.repository.get_by_id(high_late.id)
        assert (
            updated_urgent is not None
            and updated_medium is not None
            and updated_high is not None
        )

        # Earliest deadline should be first
        self.assertEqual(updated_urgent.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        # Middle deadline should be second
        self.assertEqual(updated_medium.planned_start, datetime(2025, 10, 21, 9, 0, 0))
        # Latest deadline should be last
        self.assertEqual(updated_high.planned_start, datetime(2025, 10, 22, 9, 0, 0))


if __name__ == "__main__":
    unittest.main()
