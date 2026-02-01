"""Tests for workload strategies.

Strategies are used directly for workload calculation:
- ActualScheduleStrategy: For Gantt charts (honors manual schedules)
- WeekdayOnlyStrategy: For task creation/update (weekdays only)
"""

from unittest.mock import Mock

from taskdog_core.application.queries.workload._strategies import (
    ActualScheduleStrategy,
)


class TestActualScheduleStrategy:
    """Test cases for ActualScheduleStrategy (replaces DisplayWorkloadCalculator tests)."""

    def test_creation_without_holiday_checker(self):
        """Test that strategy can be created without holiday checker."""
        strategy = ActualScheduleStrategy()

        # Verify no crash and strategy created
        assert strategy is not None
        assert strategy.holiday_checker is None

    def test_creation_with_holiday_checker(self):
        """Test that strategy accepts holiday checker."""
        mock_checker = Mock()
        strategy = ActualScheduleStrategy(holiday_checker=mock_checker)

        # Verify holiday checker is stored
        assert strategy.holiday_checker == mock_checker
