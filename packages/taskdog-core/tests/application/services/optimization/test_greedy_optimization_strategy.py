"""Tests for GreedyOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestGreedyOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for GreedyOptimizationStrategy."""

    algorithm_name = "greedy"

    def test_greedy_front_loads_single_task(self):
        """Test that greedy strategy front-loads a single task."""
        # Create task with 12h duration - should fill 2 days with 6h each
        task = self.create_task(
            "Greedy Task",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Monday
        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify greedy front-loading
        self.assertEqual(len(result.successful_tasks), 1)

        # Should start on Monday, end on Tuesday (12h / 6h per day = 2 days)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 20, 9, 0, 0),
            expected_end=datetime(2025, 10, 21, 18, 0, 0),
        )

        # Check daily allocations: greedy fills each day to max
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        self.assertEqual(len(updated_task.daily_allocations), 2)  # Mon-Tue
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5
        )
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5
        )

    def test_greedy_handles_partial_day(self):
        """Test that greedy strategy handles partial day allocation."""
        # Create task with 10h duration - should fill: 6h (day 1) + 4h (day 2)
        task = self.create_task(
            "Partial Day Task",
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Check daily allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5
        )
        self.assertAlmostEqual(
            updated_task.daily_allocations.get(date(2025, 10, 21), 0.0), 4.0, places=5
        )

    def test_greedy_skips_weekends(self):
        """Test that greedy strategy skips weekends."""
        # Create task that spans Friday to Monday
        task = self.create_task(
            "Weekend Task",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Friday
        self.optimize_schedule(start_date=datetime(2025, 10, 24, 9, 0, 0))

        # Should start Friday, end Monday (skipping Saturday/Sunday)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 24, 9, 0, 0),
            expected_end=datetime(2025, 10, 27, 18, 0, 0),
        )

        # Verify no weekend allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        self.assertIsNone(
            updated_task.daily_allocations.get(date(2025, 10, 25))
        )  # Saturday
        self.assertIsNone(
            updated_task.daily_allocations.get(date(2025, 10, 26))
        )  # Sunday

    def test_greedy_respects_deadline(self):
        """Test that greedy strategy respects task deadlines."""
        # Create task with tight deadline (30h work but only 3 days * 6h/day = 18h available)
        self.create_task(
            "Tight Deadline",
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_greedy_respects_fixed_tasks_in_daily_limit(self):
        """Test that greedy strategy accounts for fixed tasks when calculating available hours."""
        # Create a fixed task with 4h/day allocation for 3 days (Mon-Wed)
        fixed_task = self.create_task(
            "Fixed Meeting",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
            is_fixed=True,
        )

        # Manually schedule the fixed task with specific daily allocations
        fixed_task.planned_start = datetime(2025, 10, 20, 9, 0, 0)
        fixed_task.planned_end = datetime(2025, 10, 22, 18, 0, 0)
        fixed_task.daily_allocations = {
            date(2025, 10, 20): 4.0,  # Monday: 4h
            date(2025, 10, 21): 4.0,  # Tuesday: 4h
            date(2025, 10, 22): 4.0,  # Wednesday: 4h
        }
        self.repository.save(fixed_task)

        # Create a regular task that needs 6h
        regular_task = self.create_task(
            "Regular Task",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Optimize with max_hours_per_day=6.0
        # Available hours per day: 6.0 - 4.0 (fixed) = 2.0h
        # So 6h task should take 3 days (2h * 3 = 6h)
        result = self.optimize_schedule(
            start_date=datetime(2025, 10, 20, 9, 0, 0),
            force_override=True,
        )

        # Verify regular task was scheduled
        self.assertEqual(len(result.successful_tasks), 1)

        # Refetch regular task from repository to get updated state
        updated_regular = self.repository.get_by_id(regular_task.id)
        assert updated_regular is not None

        # Verify daily allocations respect fixed task hours
        # Each day should have max 2h for regular task (6.0 - 4.0 fixed)
        self.assertAlmostEqual(
            updated_regular.daily_allocations.get(date(2025, 10, 20), 0.0),
            2.0,
            places=5,
        )
        self.assertAlmostEqual(
            updated_regular.daily_allocations.get(date(2025, 10, 21), 0.0),
            2.0,
            places=5,
        )
        self.assertAlmostEqual(
            updated_regular.daily_allocations.get(date(2025, 10, 22), 0.0),
            2.0,
            places=5,
        )

        # Verify total daily allocations don't exceed max_hours_per_day
        for date_str, hours in result.daily_allocations.items():
            self.assertLessEqual(
                hours,
                6.0,
                f"Total hours on {date_str} ({hours}h) exceeds max_hours_per_day (6.0h)",
            )


if __name__ == "__main__":
    unittest.main()
