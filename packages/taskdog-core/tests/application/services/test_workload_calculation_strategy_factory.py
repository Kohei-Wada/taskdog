"""Tests for workload calculator classes (replaces factory tests).

The WorkloadCalculationStrategyFactory has been replaced by specialized
calculator classes:
- OptimizationWorkloadCalculator: For optimization (uses WeekdayOnlyStrategy)
- DisplayWorkloadCalculator: For display (uses ActualScheduleStrategy)
"""

from unittest.mock import Mock

from taskdog_core.application.queries.workload import (
    DisplayWorkloadCalculator,
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


class TestDisplayWorkloadCalculator:
    """Test cases for DisplayWorkloadCalculator."""

    def test_uses_actual_schedule_strategy(self):
        """Test that display calculator uses ActualScheduleStrategy."""
        calculator = DisplayWorkloadCalculator()

        # Verify strategy type
        assert isinstance(calculator.strategy, ActualScheduleStrategy)

    def test_with_holiday_checker(self):
        """Test that display calculator accepts holiday checker."""
        mock_checker = Mock()
        calculator = DisplayWorkloadCalculator(holiday_checker=mock_checker)

        # Verify holiday checker is passed to strategy
        assert calculator.strategy.holiday_checker == mock_checker

    def test_without_holiday_checker(self):
        """Test that display calculator works without holiday checker."""
        calculator = DisplayWorkloadCalculator()

        # Verify no crash and calculator created
        assert calculator is not None
        assert calculator.strategy.holiday_checker is None
