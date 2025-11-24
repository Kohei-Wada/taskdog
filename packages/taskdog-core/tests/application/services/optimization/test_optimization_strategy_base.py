"""Tests for OptimizationStrategy base class helper methods."""

import unittest
from datetime import date, datetime

from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class TestOptimizationStrategyHelpers(unittest.TestCase):
    """Test cases for OptimizationStrategy base class helper methods.

    These tests verify the protected helper methods that were extracted
    from individual strategy classes to eliminate code duplication.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Use GreedyOptimizationStrategy as a concrete implementation
        # to test the base class methods (default hours: 9-18)
        self.strategy = GreedyOptimizationStrategy(
            default_start_hour=9, default_end_hour=18
        )

    def test_calculate_available_hours_with_no_allocation(self):
        """Test available hours calculation when no hours are allocated."""
        daily_allocations = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 8.0)

    def test_calculate_available_hours_with_partial_allocation(self):
        """Test available hours when some hours are already allocated."""
        daily_allocations = {date(2025, 10, 20): 3.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 5.0)  # 8.0 - 3.0

    def test_calculate_available_hours_fully_allocated(self):
        """Test available hours when day is fully allocated."""
        daily_allocations = {date(2025, 10, 20): 8.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 0.0)

    def test_calculate_available_hours_today_with_remaining_hours(self):
        """Test available hours for today with remaining work hours."""
        daily_allocations = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 14:00 (2:00 PM)
        # End hour: 18:00 (6:00 PM)
        # Remaining: 4.0 hours
        current_time = datetime(2025, 10, 20, 14, 0, 0)

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 4.0)  # min(8.0, 4.0)

    def test_calculate_available_hours_today_with_allocation_and_time(self):
        """Test available hours for today considering both allocation and time."""
        daily_allocations = {date(2025, 10, 20): 2.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 14:00 (2:00 PM)
        # End hour: 18:00 (6:00 PM)
        # Available from max: 8.0 - 2.0 = 6.0 hours
        # Remaining time: 4.0 hours
        # Result: min(6.0, 4.0) = 4.0
        current_time = datetime(2025, 10, 20, 14, 0, 0)

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 4.0)

    def test_calculate_available_hours_today_past_end_hour(self):
        """Test available hours for today when past end hour."""
        daily_allocations = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 19:00 (7:00 PM) - past end hour (18:00)
        current_time = datetime(2025, 10, 20, 19, 0, 0)

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 0.0)  # No time remaining today

    def test_calculate_available_hours_with_minutes(self):
        """Test available hours calculation with fractional hours (minutes)."""
        daily_allocations = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 14:30 (2:30 PM)
        # End hour: 18:00 (6:00 PM)
        # Remaining: 3.5 hours
        current_time = datetime(2025, 10, 20, 14, 30, 0)

        available = self.strategy._calculate_available_hours(
            daily_allocations, date_obj, max_hours_per_day, current_time
        )

        self.assertEqual(available, 3.5)

    def test_set_planned_times(self):
        """Test setting planned start, end, and daily allocations on task."""
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            estimated_duration=10.0,
        )
        schedule_start = datetime(2025, 10, 20, 0, 0, 0)  # Will be set to 9:00
        schedule_end = datetime(2025, 10, 22, 0, 0, 0)  # Will be set to 18:00
        task_daily_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 3.0,
            date(2025, 10, 22): 2.0,
        }

        self.strategy._set_planned_times(
            task, schedule_start, schedule_end, task_daily_allocations
        )

        # Verify planned_start is set to 9:00 AM
        self.assertEqual(task.planned_start, datetime(2025, 10, 20, 9, 0, 0))

        # Verify planned_end is set to 6:00 PM
        self.assertEqual(task.planned_end, datetime(2025, 10, 22, 18, 0, 0))

        # Verify daily allocations are set
        self.assertEqual(task.daily_allocations, task_daily_allocations)
        self.assertEqual(len(task.daily_allocations), 3)
        self.assertEqual(task.daily_allocations[date(2025, 10, 20)], 5.0)
        self.assertEqual(task.daily_allocations[date(2025, 10, 21)], 3.0)
        self.assertEqual(task.daily_allocations[date(2025, 10, 22)], 2.0)

    def test_set_planned_times_preserves_date(self):
        """Test that _set_planned_times preserves the date but changes time."""
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            estimated_duration=5.0,
        )
        # Original times with different hours
        schedule_start = datetime(2025, 10, 15, 14, 30, 45)
        schedule_end = datetime(2025, 10, 16, 16, 45, 30)
        task_daily_allocations = {
            date(2025, 10, 15): 3.0,
            date(2025, 10, 16): 2.0,
        }

        self.strategy._set_planned_times(
            task, schedule_start, schedule_end, task_daily_allocations
        )

        # Date should be preserved, but time should be set to default hours
        self.assertEqual(task.planned_start.date(), schedule_start.date())  # Same date
        self.assertEqual(task.planned_start.hour, 9)  # Default start hour
        self.assertEqual(task.planned_start.minute, 0)
        self.assertEqual(task.planned_start.second, 0)

        self.assertEqual(task.planned_end.date(), schedule_end.date())  # Same date
        self.assertEqual(task.planned_end.hour, 18)  # Default end hour
        self.assertEqual(task.planned_end.minute, 0)
        self.assertEqual(task.planned_end.second, 0)

    def test_rollback_allocations(self):
        """Test rolling back allocations from daily_allocations."""
        daily_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 8.0,
            date(2025, 10, 22): 3.0,
        }
        task_allocations = {
            date(2025, 10, 20): 2.0,
            date(2025, 10, 21): 3.0,
            date(2025, 10, 22): 1.0,
        }

        self.strategy._rollback_allocations(daily_allocations, task_allocations)

        # Verify allocations are rolled back
        self.assertEqual(daily_allocations[date(2025, 10, 20)], 3.0)  # 5.0 - 2.0
        self.assertEqual(daily_allocations[date(2025, 10, 21)], 5.0)  # 8.0 - 3.0
        self.assertEqual(daily_allocations[date(2025, 10, 22)], 2.0)  # 3.0 - 1.0

    def test_rollback_allocations_to_zero(self):
        """Test rolling back allocations that result in zero."""
        daily_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 3.0,
        }
        task_allocations = {
            date(2025, 10, 20): 5.0,  # Complete rollback
            date(2025, 10, 21): 3.0,  # Complete rollback
        }

        self.strategy._rollback_allocations(daily_allocations, task_allocations)

        # Verify allocations are rolled back to zero
        self.assertEqual(daily_allocations[date(2025, 10, 20)], 0.0)
        self.assertEqual(daily_allocations[date(2025, 10, 21)], 0.0)

    def test_rollback_allocations_partial(self):
        """Test rolling back only some dates."""
        daily_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 8.0,
            date(2025, 10, 22): 3.0,
        }
        task_allocations = {
            date(2025, 10, 20): 2.0,
            # No rollback for 2025-10-21
            date(2025, 10, 22): 1.0,
        }

        self.strategy._rollback_allocations(daily_allocations, task_allocations)

        # Verify only specified dates are rolled back
        self.assertEqual(daily_allocations[date(2025, 10, 20)], 3.0)  # 5.0 - 2.0
        self.assertEqual(daily_allocations[date(2025, 10, 21)], 8.0)  # Unchanged
        self.assertEqual(daily_allocations[date(2025, 10, 22)], 2.0)  # 3.0 - 1.0

    def test_rollback_allocations_empty(self):
        """Test rolling back with empty task allocations."""
        daily_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 8.0,
        }
        task_allocations = {}  # Empty - nothing to rollback

        # Should not raise any errors
        self.strategy._rollback_allocations(daily_allocations, task_allocations)

        # Verify allocations are unchanged
        self.assertEqual(daily_allocations[date(2025, 10, 20)], 5.0)
        self.assertEqual(daily_allocations[date(2025, 10, 21)], 8.0)


if __name__ == "__main__":
    unittest.main()
