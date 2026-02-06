"""Tests for allocation helper functions."""

from datetime import date, datetime

from taskdog_core.application.services.optimization.allocation_helpers import (
    SCHEDULE_END_TIME,
    SCHEDULE_START_TIME,
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

    def test_calculate_available_hours_with_no_allocation(self):
        """Test available hours calculation when no hours are allocated."""
        daily_allocations: dict[date, float] = {}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
        )

        assert available == 8.0

    def test_calculate_available_hours_with_partial_allocation(self):
        """Test available hours when some hours are already allocated."""
        daily_allocations = {date(2025, 10, 20): 3.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
        )

        assert available == 5.0  # 8.0 - 3.0

    def test_calculate_available_hours_fully_allocated(self):
        """Test available hours when day is fully allocated."""
        daily_allocations = {date(2025, 10, 20): 8.0}
        date_obj = date(2025, 10, 20)
        max_hours_per_day = 8.0

        available = calculate_available_hours(
            daily_allocations,
            date_obj,
            max_hours_per_day,
        )

        assert available == 0.0

    def test_set_planned_times(self):
        """Test setting planned start, end, and daily allocations on task."""
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            estimated_duration=10.0,
        )
        schedule_start = datetime(2025, 10, 20, 0, 0, 0)
        schedule_end = datetime(2025, 10, 22, 0, 0, 0)
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
        )

        # Verify planned_start is set to 00:00:00
        assert task.planned_start == datetime(2025, 10, 20, 0, 0, 0)

        # Verify planned_end is set to 23:59:59
        assert task.planned_end == datetime(2025, 10, 22, 23, 59, 59)

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
        )

        # Date should be preserved, but time should be set to schedule constants
        assert task.planned_start is not None
        assert task.planned_start.date() == schedule_start.date()  # Same date
        assert task.planned_start.hour == SCHEDULE_START_TIME.hour
        assert task.planned_start.minute == SCHEDULE_START_TIME.minute
        assert task.planned_start.second == SCHEDULE_START_TIME.second

        assert task.planned_end is not None
        assert task.planned_end.date() == schedule_end.date()  # Same date
        assert task.planned_end.hour == SCHEDULE_END_TIME.hour
        assert task.planned_end.minute == SCHEDULE_END_TIME.minute
        assert task.planned_end.second == SCHEDULE_END_TIME.second

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
