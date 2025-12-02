"""Tests for WorkloadCalculator query service."""

from datetime import date, datetime, timedelta

import pytest

from taskdog_core.application.queries.strategies.workload_calculation_strategy import (
    ActualScheduleStrategy,
)
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestWorkloadCalculator:
    """Test cases for WorkloadCalculator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.calculator = WorkloadCalculator()

    def test_calculate_daily_workload_single_task(self):
        """Test workload calculation with a single task."""
        # Task from Monday to Friday (5 weekdays), 10 hours estimated
        # Expected with equal distribution: 10h / 5 days = 2h per day
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Equal distribution: 2h per day on all weekdays
        assert result[date(2025, 1, 6)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 7)] == pytest.approx(2.0, abs=0.01)  # Tuesday
        assert result[date(2025, 1, 8)] == pytest.approx(2.0, abs=0.01)  # Wednesday
        assert result[date(2025, 1, 9)] == pytest.approx(2.0, abs=0.01)  # Thursday
        assert result[date(2025, 1, 10)] == pytest.approx(2.0, abs=0.01)  # Friday

    def test_calculate_daily_workload_excludes_weekends(self):
        """Test that weekends are excluded from workload calculation."""
        # Task spanning a weekend (Friday to Tuesday)
        # Expected with equal distribution: 6h / 3 weekdays (Fri, Mon, Tue) = 2h per day
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 10, 9, 0, 0),  # Friday
            planned_end=datetime(2025, 1, 14, 18, 0, 0),  # Tuesday (next week)
            estimated_duration=6.0,  # 3 weekdays: Fri, Mon, Tue
        )

        start_date = date(2025, 1, 10)  # Friday
        end_date = date(2025, 1, 14)  # Tuesday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Equal distribution: 2h per weekday, weekends excluded
        assert result[date(2025, 1, 10)] == pytest.approx(2.0, abs=0.01)  # Friday
        assert result[date(2025, 1, 11)] == pytest.approx(0.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(0.0, abs=0.01)  # Sunday
        assert result[date(2025, 1, 13)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(2.0, abs=0.01)  # Tuesday

    def test_calculate_daily_workload_multiple_tasks(self):
        """Test workload calculation with multiple overlapping tasks."""
        # With equal distribution:
        # Task 1 (6h, Mon-Wed, 3 weekdays): 2h per day
        # Task 2 (9h, Wed-Fri, 3 weekdays): 3h per day
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: Wednesday to Friday, 9 hours
        task2 = Task(
            id=2,
            name="Task 2",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Task 1: 2h on Mon, Tue, Wed
        # Task 2: 3h on Wed, Thu, Fri
        # Wednesday has both: 2h + 3h = 5h
        assert result[date(2025, 1, 6)] == pytest.approx(
            2.0, abs=0.01
        )  # Monday (task1)
        assert result[date(2025, 1, 7)] == pytest.approx(
            2.0, abs=0.01
        )  # Tuesday (task1)
        assert result[date(2025, 1, 8)] == pytest.approx(
            5.0, abs=0.01
        )  # Wednesday (task1 + task2)
        assert result[date(2025, 1, 9)] == pytest.approx(
            3.0, abs=0.01
        )  # Thursday (task2)
        assert result[date(2025, 1, 10)] == pytest.approx(
            3.0, abs=0.01
        )  # Friday (task2)

    def test_calculate_daily_workload_no_estimated_duration(self):
        """Test that tasks without estimated duration are skipped."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),
            planned_end=datetime(2025, 1, 10, 18, 0, 0),
            estimated_duration=None,  # No estimate
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            assert result[current_date] == 0.0

    def test_calculate_daily_workload_no_planned_dates(self):
        """Test that tasks without planned dates are skipped."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=None,
            planned_end=None,
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            assert result[current_date] == 0.0

    def test_calculate_daily_workload_task_outside_range(self):
        """Test that tasks outside the date range are handled correctly."""
        # Task from Feb 1-5, but we're looking at Jan 6-10
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 2, 1, 9, 0, 0),
            planned_end=datetime(2025, 2, 5, 18, 0, 0),
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours (task is outside range)
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            assert result[current_date] == 0.0

    def test_calculate_daily_workload_excludes_completed_tasks(self):
        """Test that completed tasks are excluded from workload calculation."""
        # Task 1: PENDING task (Monday to Wednesday, 6 hours, 3 weekdays)
        # With equal distribution: 2h per day
        task1 = Task(
            id=1,
            name="Pending Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: COMPLETED task (Wednesday to Friday, 9 hours) - should be excluded
        task2 = Task(
            id=2,
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Only task1 (PENDING) should be counted with equal distribution
        # Task2 (COMPLETED) is excluded entirely
        assert result[date(2025, 1, 6)] == pytest.approx(
            2.0, abs=0.01
        )  # Monday (task1)
        assert result[date(2025, 1, 7)] == pytest.approx(
            2.0, abs=0.01
        )  # Tuesday (task1)
        assert result[date(2025, 1, 8)] == pytest.approx(
            2.0, abs=0.01
        )  # Wednesday (task1)
        assert result[date(2025, 1, 9)] == pytest.approx(
            0.0, abs=0.01
        )  # Thursday (task2 excluded)
        assert result[date(2025, 1, 10)] == pytest.approx(
            0.0, abs=0.01
        )  # Friday (task2 excluded)

    def test_calculate_daily_workload_with_daily_allocations(self):
        """Test workload calculation using daily_allocations from optimization."""
        # Task with daily_allocations (from optimization)
        # Monday: 5h, Tuesday: 1h
        task = Task(
            id=1,
            name="Optimized Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 7, 18, 0, 0),  # Tuesday
            estimated_duration=6.0,
            daily_allocations={
                date(2025, 1, 6): 5.0,  # Monday
                date(2025, 1, 7): 1.0,  # Tuesday
            },
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Should use daily_allocations instead of equal distribution
        assert result[date(2025, 1, 6)] == pytest.approx(5.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 7)] == pytest.approx(1.0, abs=0.01)  # Tuesday
        assert result[date(2025, 1, 8)] == pytest.approx(0.0, abs=0.01)  # Wednesday
        assert result[date(2025, 1, 9)] == pytest.approx(0.0, abs=0.01)  # Thursday
        assert result[date(2025, 1, 10)] == pytest.approx(0.0, abs=0.01)  # Friday

    def test_calculate_daily_workload_fallback_to_equal_distribution(self):
        """Test that calculator falls back to equal distribution when daily_allocations is empty."""
        # Task without daily_allocations (backward compatibility)
        task = Task(
            id=1,
            name="Legacy Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
            daily_allocations={},  # Empty dict (no optimizer data)
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Should fall back to equal distribution: 6h / 3 weekdays = 2h per day
        assert result[date(2025, 1, 6)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 7)] == pytest.approx(2.0, abs=0.01)  # Tuesday
        assert result[date(2025, 1, 8)] == pytest.approx(2.0, abs=0.01)  # Wednesday
        assert result[date(2025, 1, 9)] == pytest.approx(0.0, abs=0.01)  # Thursday
        assert result[date(2025, 1, 10)] == pytest.approx(0.0, abs=0.01)  # Friday

    def test_calculate_daily_workload_excludes_archived_tasks(self):
        """Test that archived tasks are excluded from workload calculation."""
        # Task 1: PENDING task (Monday to Wednesday, 6 hours, 3 weekdays)
        # With equal distribution: 2h per day
        task1 = Task(
            id=1,
            name="Active Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: PENDING but archived task (Wednesday to Friday, 9 hours) - should be excluded
        task2 = Task(
            id=2,
            name="Archived Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
            is_archived=True,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Only task1 (active) should be counted with equal distribution
        # Task2 (archived) is excluded entirely
        assert result[date(2025, 1, 6)] == pytest.approx(
            2.0, abs=0.01
        )  # Monday (task1)
        assert result[date(2025, 1, 7)] == pytest.approx(
            2.0, abs=0.01
        )  # Tuesday (task1)
        assert result[date(2025, 1, 8)] == pytest.approx(
            2.0, abs=0.01
        )  # Wednesday (task1)
        assert result[date(2025, 1, 9)] == pytest.approx(
            0.0, abs=0.01
        )  # Thursday (task2 excluded)
        assert result[date(2025, 1, 10)] == pytest.approx(
            0.0, abs=0.01
        )  # Friday (task2 excluded)


class TestWorkloadCalculatorWithActualScheduleStrategy:
    """Test cases for WorkloadCalculator with ActualScheduleStrategy.

    These tests verify that when using ActualScheduleStrategy, workload
    calculations include weekends and honor manually scheduled tasks.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with ActualScheduleStrategy."""
        self.calculator = WorkloadCalculator(ActualScheduleStrategy())

    def test_calculate_daily_workload_prioritizes_weekdays_in_period(self):
        """Test that ActualScheduleStrategy prioritizes weekdays within the period."""
        # Task spanning Friday to Tuesday (5 days total, 3 weekdays)
        # Expected: 10h / 3 weekdays = 3.33h per weekday
        task = Task(
            id=1,
            name="Weekday Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 10, 9, 0, 0),  # Friday
            planned_end=datetime(2025, 1, 14, 18, 0, 0),  # Tuesday
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 10)  # Friday
        end_date = date(2025, 1, 14)  # Tuesday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Weekdays should have 3.33h, weekends should be 0
        assert result[date(2025, 1, 10)] == pytest.approx(3.33, abs=0.01)  # Friday
        assert result[date(2025, 1, 11)] == pytest.approx(0.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(0.0, abs=0.01)  # Sunday
        assert result[date(2025, 1, 13)] == pytest.approx(3.33, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(3.33, abs=0.01)  # Tuesday

    def test_calculate_daily_workload_weekend_only_task(self):
        """Test that weekend-only tasks are properly calculated."""
        # Task scheduled only on Saturday-Sunday
        task = Task(
            id=1,
            name="Weekend Only Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 12, 18, 0, 0),  # Sunday
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 10)  # Friday
        end_date = date(2025, 1, 14)  # Tuesday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Weekend should have hours, weekdays should be 0
        # 10h / 2 days = 5h per day
        assert result[date(2025, 1, 10)] == pytest.approx(0.0, abs=0.01)  # Friday
        assert result[date(2025, 1, 11)] == pytest.approx(5.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(5.0, abs=0.01)  # Sunday
        assert result[date(2025, 1, 13)] == pytest.approx(0.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(0.0, abs=0.01)  # Tuesday

    def test_calculate_daily_workload_single_weekend_day(self):
        """Test that single weekend day tasks are properly calculated."""
        # Task scheduled only on Saturday
        task = Task(
            id=1,
            name="Saturday Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 11, 18, 0, 0),  # Same Saturday
            estimated_duration=8.0,
        )

        start_date = date(2025, 1, 10)  # Friday
        end_date = date(2025, 1, 14)  # Tuesday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Only Saturday should have hours
        assert result[date(2025, 1, 10)] == pytest.approx(0.0, abs=0.01)  # Friday
        assert result[date(2025, 1, 11)] == pytest.approx(8.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(0.0, abs=0.01)  # Sunday
        assert result[date(2025, 1, 13)] == pytest.approx(0.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(0.0, abs=0.01)  # Tuesday

    def test_calculate_daily_workload_mixed_weekday_weekend_tasks(self):
        """Test workload with both weekday and weekend tasks."""
        # Task 1: Weekday task (Monday to Wednesday, 6 hours)
        task1 = Task(
            id=1,
            name="Weekday Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: Weekend task (Saturday to Sunday, 10 hours)
        task2 = Task(
            id=2,
            name="Weekend Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 12, 18, 0, 0),  # Sunday
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 12)  # Sunday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Task 1: 6h / 3 days = 2h per day (Mon-Wed)
        # Task 2: 10h / 2 days = 5h per day (Sat-Sun)
        assert result[date(2025, 1, 6)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 7)] == pytest.approx(2.0, abs=0.01)  # Tuesday
        assert result[date(2025, 1, 8)] == pytest.approx(2.0, abs=0.01)  # Wednesday
        assert result[date(2025, 1, 9)] == pytest.approx(0.0, abs=0.01)  # Thursday
        assert result[date(2025, 1, 10)] == pytest.approx(0.0, abs=0.01)  # Friday
        assert result[date(2025, 1, 11)] == pytest.approx(5.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(5.0, abs=0.01)  # Sunday
