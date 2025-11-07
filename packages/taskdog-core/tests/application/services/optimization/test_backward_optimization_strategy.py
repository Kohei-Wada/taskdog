"""Tests for BackwardOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestBackwardOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for BackwardOptimizationStrategy."""

    algorithm_name = "backward"

    def test_backward_schedules_close_to_deadline(self):
        """Test that backward strategy schedules tasks close to deadline."""
        # Create task with 6h duration and deadline on Friday
        # Should be scheduled on Friday (as late as possible)
        task = self.create_task(
            "JIT Task",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)

        # Should be scheduled on Friday (closest to deadline)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 24, 9, 0, 0),
            expected_end=datetime(2025, 10, 24, 18, 0, 0),
        )

        # Re-fetch task from repository to verify allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        # All 6h allocated on Friday
        self.assertEqual(updated_task.daily_allocations[date(2025, 10, 24)], 6.0)

    def test_backward_spans_backward_from_deadline(self):
        """Test that backward strategy fills backwards when task doesn't fit in one day."""
        # Create task with 12h duration and deadline on Friday
        # With 6h/day max, needs 2 days: Thursday and Friday
        task = self.create_task(
            "Multi-day JIT",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)

        # Should start on Thursday, end on Friday
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 23, 9, 0, 0),
            expected_end=datetime(2025, 10, 24, 18, 0, 0),
        )

        # 6h on Thursday, 6h on Friday
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        self.assertEqual(updated_task.daily_allocations[date(2025, 10, 23)], 6.0)
        self.assertEqual(updated_task.daily_allocations[date(2025, 10, 24)], 6.0)

    def test_backward_without_deadline_schedules_near_future(self):
        """Test that tasks without deadline are scheduled in near future (1 week)."""
        # Create task without deadline
        self.create_task("No Deadline Task", estimated_duration=6.0)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should be scheduled (using default 1-week period)
        self.assert_task_scheduled(task)

        # Should be 6h total
        self.assert_total_allocated_hours(task, 6.0)

    def test_backward_respects_max_hours_per_day(self):
        """Test that backward strategy respects max_hours_per_day constraint."""
        # Create task with 18h duration and deadline 3 weekdays away
        # With 6h/day max, should use all 3 days
        task = self.create_task(
            "Max Hours Task",
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)

        # Should respect max_hours_per_day
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        for _date_str, hours in updated_task.daily_allocations.items():
            self.assertLessEqual(hours, 6.0)

        # Total should be 18h
        self.assert_total_allocated_hours(task, 18.0)

        # Should use Mon, Tue, Wed (backwards from Wed)
        self.assertEqual(len(updated_task.daily_allocations), 3)

    def test_backward_handles_multiple_tasks(self):
        """Test backward strategy with multiple tasks (furthest deadline first)."""
        # Create two tasks with different deadlines
        task1 = self.create_task(
            "Task 1", estimated_duration=6.0, deadline=datetime(2025, 10, 24, 18, 0, 0)
        )
        task2 = self.create_task(
            "Task 2", estimated_duration=6.0, deadline=datetime(2025, 10, 22, 18, 0, 0)
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task 1 (further deadline) is processed first, scheduled on Friday
        updated_task1 = self.repository.get_by_id(task1.id)
        assert updated_task1 is not None
        self.assertEqual(updated_task1.planned_start, datetime(2025, 10, 24, 9, 0, 0))

        # Task 2 (closer deadline) is processed second, scheduled on Wednesday
        updated_task2 = self.repository.get_by_id(task2.id)
        assert updated_task2 is not None
        self.assertEqual(updated_task2.planned_start, datetime(2025, 10, 22, 9, 0, 0))

    def test_backward_fails_when_deadline_before_start(self):
        """Test that backward strategy fails when deadline is before start date."""
        # Create task with deadline before start date
        self.create_task(
            "Past Deadline",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 19, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Task should not be scheduled
        self.assertEqual(len(result.successful_tasks), 0)

    def test_backward_skips_weekends(self):
        """Test that backward strategy skips weekends when allocating."""
        # Create task with 6h duration and deadline on Monday
        # Should skip weekend and allocate on Monday
        task = self.create_task(
            "Weekend Skip",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 27, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)

        # Should be scheduled on Monday (deadline day)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 27, 9, 0, 0),
            expected_end=datetime(2025, 10, 27, 18, 0, 0),
        )

        # Only Monday in allocations (no weekend days)
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        self.assertEqual(len(updated_task.daily_allocations), 1)
        self.assertIn(date(2025, 10, 27), updated_task.daily_allocations)


if __name__ == "__main__":
    unittest.main()
