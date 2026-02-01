"""Tests for workload strategies and calculator classes.

The DisplayWorkloadCalculator has been removed - use ActualScheduleStrategy directly.
The OptimizationWorkloadCalculator is kept for backward compatibility.
"""

from unittest.mock import Mock

from taskdog_core.application.queries.workload import (
    OptimizationWorkloadCalculator,
)
from taskdog_core.application.queries.workload._strategies import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
)


class TestOptimizationWorkloadCalculator:
    """Test cases for OptimizationWorkloadCalculator."""

    def test_uses_weekday_only_strategy(self):
        """Test that optimization calculator uses WeekdayOnlyStrategy."""
        calculator = OptimizationWorkloadCalculator()

        # Verify strategy type
        assert isinstance(calculator.strategy, WeekdayOnlyStrategy)

    def test_with_holiday_checker(self):
        """Test that optimization calculator accepts holiday checker."""
        mock_checker = Mock()
        calculator = OptimizationWorkloadCalculator(holiday_checker=mock_checker)

        # Verify holiday checker is passed to strategy
        assert calculator.strategy.holiday_checker == mock_checker

    def test_without_holiday_checker(self):
        """Test that optimization calculator works without holiday checker."""
        calculator = OptimizationWorkloadCalculator()

        # Verify no crash and calculator created
        assert calculator is not None
        assert calculator.strategy.holiday_checker is None


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
