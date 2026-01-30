"""Tests for BalancedOptimizationStrategy."""

from datetime import date, datetime, time

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.services.optimization.balanced_optimization_strategy import (
    BalancedOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.holiday_checker import IHolidayChecker
from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestBalancedOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for BalancedOptimizationStrategy."""

    algorithm_name = "balanced"

    def test_balanced_distributes_evenly_with_deadline(self):
        """Test that balanced strategy distributes hours evenly across available period."""
        # Create task with 10h duration and deadline 5 weekdays away
        # Monday to Friday = 5 weekdays, should allocate 2h/day
        task = self.create_task(
            "Balanced Task",
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify balanced distribution
        assert len(result.successful_tasks) == 1

        # Should start Monday, end Friday
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 20, 9, 0, 0),
            expected_end=datetime(2025, 10, 24, 18, 0, 0),
        )

        # Check daily allocations: 10h / 5 days = 2h/day
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert len(updated_task.daily_allocations) == 5  # Mon-Fri
        for _date_str, hours in updated_task.daily_allocations.items():
            assert abs(hours - 2.0) < 1e-5

    def test_balanced_without_deadline_uses_default_period(self):
        """Test that tasks without deadline use a default period (2 weeks)."""
        # Create task without deadline
        self.create_task("No Deadline Task", estimated_duration=20.0)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify task was scheduled
        assert len(result.successful_tasks) == 1
        task = result.successful_tasks[0]

        # Should be scheduled (using default 2-week period)
        self.assert_task_scheduled(task)

        # With 20h over 2 weeks (10 weekdays), should allocate 2h/day
        self.assert_total_allocated_hours(task, 20.0)

    def test_balanced_respects_max_hours_per_day(self):
        """Test that balanced strategy respects max_hours_per_day constraint."""
        # Create task that would need more days due to max_hours_per_day
        # 12h over 5 weekdays = 2.4h/day, but we set max to 6h/day (plenty)
        task = self.create_task(
            "Constrained Task",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        assert len(result.successful_tasks) == 1

        # Should respect max_hours_per_day
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        for _date_str, hours in updated_task.daily_allocations.items():
            assert hours <= 6.0

        # Total should still be 12h
        self.assert_total_allocated_hours(task, 12.0)

    def test_balanced_handles_multiple_tasks(self):
        """Test balanced strategy with multiple tasks."""
        # Create two tasks with deadlines
        tasks = []
        tasks.append(
            self.create_task(
                "Task 1",
                priority=200,
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 22, 18, 0, 0),  # Wednesday
            )
        )
        tasks.append(
            self.create_task(
                "Task 2",
                priority=100,
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
            )
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Each task should have daily allocations
        for task in tasks:
            self.assert_total_allocated_hours(task, 6.0)

    def test_balanced_fails_when_deadline_too_tight(self):
        """Test that balanced strategy returns None when deadline cannot be met."""
        # Create task with 10h duration but only 1 weekday until deadline
        # Even with 6h/day max, cannot fit 10h in 1 day
        self.create_task(
            "Impossible Task",
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 20, 18, 0, 0),  # Same day as start
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Task should not be scheduled
        assert len(result.successful_tasks) == 0


class TestBalancedOptimizationStrategyWithHolidays:
    """Test cases for BalancedOptimizationStrategy with holiday handling."""

    def test_planned_end_matches_daily_allocations_with_holidays(self):
        """Test that planned_end matches the last date in daily_allocations when holidays are involved.

        This test verifies the fix for the bug where multi-pass allocation
        with holidays caused planned_end to not match daily_allocations.
        """

        # Mock holiday checker that marks 2026-01-01 as holiday
        class MockHolidayChecker(IHolidayChecker):
            def is_holiday(self, d: date) -> bool:
                return d == date(2026, 1, 1)

            def get_holidays_in_range(self, start: date, end: date) -> set[date]:
                if date(2026, 1, 1) >= start and date(2026, 1, 1) <= end:
                    return {date(2026, 1, 1)}
                return set()

        holiday_checker = MockHolidayChecker()

        # Task with 8 hours, deadline on 1/3 (only 12/31 and 1/2 available due to holiday)
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            deadline=datetime(2026, 1, 3, 18, 0, 0),
        )

        # Create params with max 6 hours per day (forces multi-pass allocation)
        params = OptimizeParams(
            start_date=datetime(2025, 12, 31, 9, 0, 0),
            max_hours_per_day=6.0,
            holiday_checker=holiday_checker,
            current_time=None,
        )
        daily_allocations: dict[date, float] = {}

        strategy = BalancedOptimizationStrategy(
            default_start_time=time(9, 0), default_end_time=time(18, 0)
        )
        result = strategy._allocate_task(task, daily_allocations, params)

        assert result is not None
        assert result.daily_allocations is not None
        assert result.planned_end is not None

        # The key assertion: planned_end should match the last date in daily_allocations
        last_allocation_date = max(result.daily_allocations.keys())
        planned_end_date = result.planned_end.date()
        assert last_allocation_date == planned_end_date, (
            f"planned_end ({planned_end_date}) should match "
            f"last allocation date ({last_allocation_date})"
        )

        # Verify holiday is skipped (no allocation on 2026-01-01)
        assert date(2026, 1, 1) not in result.daily_allocations

    def test_planned_end_correct_without_holidays(self):
        """Test that planned_end is correct even without holidays."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2026, 1, 10, 18, 0, 0),
        )

        params = OptimizeParams(
            start_date=datetime(2025, 12, 31, 9, 0, 0),
            max_hours_per_day=6.0,
            holiday_checker=None,
            current_time=None,
        )
        daily_allocations: dict[date, float] = {}

        strategy = BalancedOptimizationStrategy(
            default_start_time=time(9, 0), default_end_time=time(18, 0)
        )
        result = strategy._allocate_task(task, daily_allocations, params)

        assert result is not None
        assert result.daily_allocations is not None
        assert result.planned_end is not None

        # planned_end should match the last date in daily_allocations
        last_allocation_date = max(result.daily_allocations.keys())
        planned_end_date = result.planned_end.date()
        assert last_allocation_date == planned_end_date
