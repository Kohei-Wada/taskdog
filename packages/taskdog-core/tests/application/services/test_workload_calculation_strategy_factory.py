"""Tests for WorkloadCalculationStrategyFactory."""

from unittest.mock import Mock

from taskdog_core.application.queries.strategies.workload_calculation_strategy import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
)
from taskdog_core.application.services.workload_calculation_strategy_factory import (
    WorkloadCalculationStrategyFactory,
)


class TestWorkloadCalculationStrategyFactory:
    """Test cases for WorkloadCalculationStrategyFactory."""

    def test_create_for_optimization_returns_weekday_only_strategy(self):
        """Test that optimization factory returns WeekdayOnlyStrategy."""
        strategy = WorkloadCalculationStrategyFactory.create_for_optimization()

        # Verify strategy type
        assert isinstance(strategy, WeekdayOnlyStrategy)

    def test_create_for_optimization_with_holiday_checker(self):
        """Test that optimization factory accepts holiday checker."""
        mock_checker = Mock()
        strategy = WorkloadCalculationStrategyFactory.create_for_optimization(
            holiday_checker=mock_checker
        )

        # Verify holiday checker is passed to strategy
        assert strategy.holiday_checker == mock_checker

    def test_create_for_optimization_without_holiday_checker(self):
        """Test that optimization factory works without holiday checker."""
        strategy = WorkloadCalculationStrategyFactory.create_for_optimization()

        # Verify no crash and strategy created
        assert strategy is not None
        assert strategy.holiday_checker is None

    def test_create_for_display_returns_actual_schedule_strategy(self):
        """Test that display factory returns ActualScheduleStrategy."""
        strategy = WorkloadCalculationStrategyFactory.create_for_display()

        # Verify strategy type
        assert isinstance(strategy, ActualScheduleStrategy)

    def test_create_for_display_with_holiday_checker(self):
        """Test that display factory accepts holiday checker."""
        mock_checker = Mock()
        strategy = WorkloadCalculationStrategyFactory.create_for_display(
            holiday_checker=mock_checker
        )

        # Verify holiday checker is passed to strategy
        assert strategy.holiday_checker == mock_checker

    def test_create_for_display_without_holiday_checker(self):
        """Test that display factory works without holiday checker."""
        strategy = WorkloadCalculationStrategyFactory.create_for_display()

        # Verify no crash and strategy created
        assert strategy is not None
        assert strategy.holiday_checker is None
