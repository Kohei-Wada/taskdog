"""Tests for workload calculation strategies.

Note: This file was refactored to test strategies directly instead of
the deprecated BaseWorkloadCalculator and DisplayWorkloadCalculator classes.
"""

from datetime import date, datetime

import pytest

from taskdog_core.application.queries.workload._strategies import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestWeekdayOnlyStrategy:
    """Test cases for WeekdayOnlyStrategy (used in optimization)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.strategy = WeekdayOnlyStrategy()

    def test_compute_from_planned_period_single_task(self):
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

        result = self.strategy.compute_from_planned_period(task)

        # Equal distribution: 2h per day on all weekdays
        assert result[date(2025, 1, 6)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 7)] == pytest.approx(2.0, abs=0.01)  # Tuesday
        assert result[date(2025, 1, 8)] == pytest.approx(2.0, abs=0.01)  # Wednesday
        assert result[date(2025, 1, 9)] == pytest.approx(2.0, abs=0.01)  # Thursday
        assert result[date(2025, 1, 10)] == pytest.approx(2.0, abs=0.01)  # Friday

    def test_compute_from_planned_period_excludes_weekends(self):
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

        result = self.strategy.compute_from_planned_period(task)

        # Equal distribution: 2h per weekday, weekends excluded
        assert result[date(2025, 1, 10)] == pytest.approx(2.0, abs=0.01)  # Friday
        assert date(2025, 1, 11) not in result  # Saturday (excluded)
        assert date(2025, 1, 12) not in result  # Sunday (excluded)
        assert result[date(2025, 1, 13)] == pytest.approx(2.0, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(2.0, abs=0.01)  # Tuesday

    def test_compute_from_planned_period_no_estimated_duration(self):
        """Test that tasks without estimated duration return empty dict."""
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

        result = self.strategy.compute_from_planned_period(task)

        assert result == {}

    def test_compute_from_planned_period_no_planned_dates(self):
        """Test that tasks without planned dates return empty dict."""
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

        result = self.strategy.compute_from_planned_period(task)

        assert result == {}


class TestActualScheduleStrategy:
    """Test cases for ActualScheduleStrategy (used for display/Gantt).

    These tests verify that ActualScheduleStrategy honors manually scheduled
    tasks while prioritizing weekdays.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with ActualScheduleStrategy."""
        self.strategy = ActualScheduleStrategy()

    def test_compute_prioritizes_weekdays_in_period(self):
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

        result = self.strategy.compute_from_planned_period(task)

        # Weekdays should have 3.33h, weekends excluded
        assert result[date(2025, 1, 10)] == pytest.approx(3.33, abs=0.01)  # Friday
        assert date(2025, 1, 11) not in result  # Saturday (excluded)
        assert date(2025, 1, 12) not in result  # Sunday (excluded)
        assert result[date(2025, 1, 13)] == pytest.approx(3.33, abs=0.01)  # Monday
        assert result[date(2025, 1, 14)] == pytest.approx(3.33, abs=0.01)  # Tuesday

    def test_compute_weekend_only_task(self):
        """Test that weekend-only tasks are properly calculated (fallback)."""
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

        result = self.strategy.compute_from_planned_period(task)

        # Weekend should have hours (fallback to all days)
        # 10h / 2 days = 5h per day
        assert result[date(2025, 1, 11)] == pytest.approx(5.0, abs=0.01)  # Saturday
        assert result[date(2025, 1, 12)] == pytest.approx(5.0, abs=0.01)  # Sunday

    def test_compute_single_weekend_day(self):
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

        result = self.strategy.compute_from_planned_period(task)

        # Only Saturday should have hours
        assert result[date(2025, 1, 11)] == pytest.approx(8.0, abs=0.01)  # Saturday
        assert len(result) == 1
