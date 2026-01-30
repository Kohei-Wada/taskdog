"""Tests for allocation helper functions."""

from datetime import date, datetime, time

import pytest

from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
)
from taskdog_core.domain.entities.task import Task


class TestOptimizationStrategyHelpers:
    """Test cases for allocation helper functions.

    These tests verify the helper functions that were extracted
    from individual strategy classes to eliminate code duplication.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.default_start_time = time(9, 0)
        self.default_end_time = time(18, 0)

    def test_calculate_available_hours_with_no_allocation(self):
        """Test available hours calculation when no hours are allocated."""
        daily_allocations: dict[date, float] = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 8.0

    def test_calculate_available_hours_with_partial_allocation(self):
        """Test available hours when some hours are already allocated."""
        daily_allocations = {date(2025, 10, 20): 3.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 5.0  # 8.0 - 3.0

    def test_calculate_available_hours_fully_allocated(self):
        """Test available hours when day is fully allocated."""
        daily_allocations = {date(2025, 10, 20): 8.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        current_time = None

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 0.0

    def test_calculate_available_hours_today_with_remaining_hours(self):
        """Test available hours for today with remaining work hours."""
        daily_allocations: dict[date, float] = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 14:00 (2:00 PM)
        # End hour: 18:00 (6:00 PM)
        # Remaining: 4.0 hours
        current_time = datetime(2025, 10, 20, 14, 0, 0)

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 4.0  # min(8.0, 4.0)

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

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 4.0

    def test_calculate_available_hours_today_past_end_hour(self):
        """Test available hours for today when past end hour."""
        daily_allocations: dict[date, float] = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 19:00 (7:00 PM) - past end hour (18:00)
        current_time = datetime(2025, 10, 20, 19, 0, 0)

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 0.0  # No time remaining today

    def test_calculate_available_hours_with_minutes(self):
        """Test available hours calculation with fractional hours (minutes)."""
        daily_allocations: dict[date, float] = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0
        # Current time: 2025-10-20 14:30 (2:30 PM)
        # End hour: 18:00 (6:00 PM)
        # Remaining: 3.5 hours
        current_time = datetime(2025, 10, 20, 14, 30, 0)

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
            current_time,
            self.default_end_time,
        )

        assert available == 3.5

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

        set_planned_times(
            task,
            schedule_start,
            schedule_end,
            task_daily_allocations,
            self.default_start_time,
            self.default_end_time,
        )

        # Verify planned_start is set to 9:00 AM
        assert task.planned_start == datetime(2025, 10, 20, 9, 0, 0)

        # Verify planned_end is set to 6:00 PM
        assert task.planned_end == datetime(2025, 10, 22, 18, 0, 0)

        # Verify daily allocations are set
        assert task.daily_allocations == task_daily_allocations
        assert len(task.daily_allocations) == 3
        assert task.daily_allocations[date(2025, 10, 20)] == 5.0
        assert task.daily_allocations[date(2025, 10, 21)] == 3.0
        assert task.daily_allocations[date(2025, 10, 22)] == 2.0

    def test_set_planned_times_preserves_date(self):
        """Test that set_planned_times preserves the date but changes time."""
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

        set_planned_times(
            task,
            schedule_start,
            schedule_end,
            task_daily_allocations,
            self.default_start_time,
            self.default_end_time,
        )

        # Date should be preserved, but time should be set to default hours
        assert task.planned_start is not None
        assert task.planned_start.date() == schedule_start.date()  # Same date
        assert task.planned_start.hour == 9  # Default start hour
        assert task.planned_start.minute == 0
        assert task.planned_start.second == 0

        assert task.planned_end is not None
        assert task.planned_end.date() == schedule_end.date()  # Same date
        assert task.planned_end.hour == 18  # Default end hour
        assert task.planned_end.minute == 0
        assert task.planned_end.second == 0

    def test_prepare_task_for_allocation_valid_task(self):
        """Test prepare_task_for_allocation with valid task."""
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            estimated_duration=10.0,
        )

        result = prepare_task_for_allocation(task)

        # Verify task copy is returned
        assert result is not None
        assert result is not task  # Should be a different object (deep copy)
        assert result.id == task.id
        assert result.name == task.name
        assert result.estimated_duration == task.estimated_duration

    def test_prepare_task_for_allocation_none_duration(self):
        """Test prepare_task_for_allocation with None duration."""
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            estimated_duration=None,
        )

        result = prepare_task_for_allocation(task)

        # Should return None for None duration
        assert result is None

    def test_prepare_task_for_allocation_is_deep_copy(self):
        """Test that prepare_task_for_allocation returns deep copy."""
        task = Task(
            id=1,
            name="Original Task",
            priority=100,
            estimated_duration=10.0,
        )

        result = prepare_task_for_allocation(task)

        assert result is not None
        # Modify the copy
        result.name = "Modified Task"
        result.priority = 200

        # Original should be unchanged
        assert task.name == "Original Task"
        assert task.priority == 100
