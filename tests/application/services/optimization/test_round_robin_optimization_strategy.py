"""Tests for RoundRobinOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestRoundRobinOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for RoundRobinOptimizationStrategy."""

    algorithm_name = "round_robin"

    def test_round_robin_distributes_hours_equally(self):
        """Test that round-robin distributes hours equally among tasks."""
        # Create two tasks with same duration
        self.create_task(
            "Task 1",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Task 2",
            priority=50,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Each task should get 3h per day (6h / 2 tasks)
        for task in result.successful_tasks:
            self.assertIsNotNone(task.daily_allocations)
            # Check first day allocation
            first_day_allocation = task.daily_allocations.get(date(2025, 10, 20), 0.0)
            self.assertAlmostEqual(first_day_allocation, 3.0, places=5)

    def test_round_robin_makes_parallel_progress(self):
        """Test that round-robin makes progress on all tasks in parallel."""
        # Create three tasks with different durations
        self.create_task(
            "Short Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Medium Task",
            priority=50,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Long Task",
            priority=25,
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # All tasks should start on the same day (parallel progress)
        for task in result.successful_tasks:
            self.assertEqual(task.planned_start, datetime(2025, 10, 20, 9, 0, 0))

    def test_round_robin_stops_allocating_after_task_completion(self):
        """Test that round-robin stops allocating to completed tasks."""
        # Create two tasks: one short, one long
        self.create_task(
            "Short Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Long Task",
            priority=50,
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        tasks_by_name = {t.name: t for t in result.successful_tasks}
        short_task = tasks_by_name["Short Task"]
        long_task = tasks_by_name["Long Task"]

        # Short task should complete earlier than long task
        self.assertLess(short_task.planned_end, long_task.planned_end)

    def test_round_robin_respects_deadlines(self):
        """Test that round-robin respects task deadlines."""
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

    def test_round_robin_skips_weekends(self):
        """Test that round-robin skips weekends."""
        # Create task that spans over a weekend
        self.create_task(
            "Weekend Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Friday
        result = self.optimize_schedule(start_date=datetime(2025, 10, 24, 9, 0, 0))

        task = result.successful_tasks[0]

        # Verify no weekend allocations
        self.assertIsNone(task.daily_allocations.get(date(2025, 10, 25)))  # Saturday
        self.assertIsNone(task.daily_allocations.get(date(2025, 10, 26)))  # Sunday

    def test_round_robin_with_single_task(self):
        """Test that round-robin works correctly with a single task."""
        # Single task should get all available hours each day
        self.create_task(
            "Single Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        task = result.successful_tasks[0]

        # Single task should get full 6h each day (not divided)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5)

    def test_round_robin_adjusts_allocation_as_tasks_complete(self):
        """Test that round-robin adjusts allocation as tasks complete."""
        # Create three tasks with staggered durations
        self.create_task(
            "Quick Task",
            priority=100,
            estimated_duration=4.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Medium Task",
            priority=50,
            estimated_duration=8.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Long Task",
            priority=25,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # Verify that tasks complete at different times
        quick_end = tasks_by_name["Quick Task"].planned_end
        medium_end = tasks_by_name["Medium Task"].planned_end
        long_end = tasks_by_name["Long Task"].planned_end

        self.assertLess(quick_end, medium_end)
        self.assertLess(medium_end, long_end)


if __name__ == "__main__":
    unittest.main()
