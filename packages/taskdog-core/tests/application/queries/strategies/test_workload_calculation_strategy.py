"""Tests for workload calculation strategies."""

import unittest
from datetime import date, datetime

from taskdog_core.application.queries.strategies.workload_calculation_strategy import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
)
from taskdog_core.domain.entities.task import Task


class MockHolidayChecker:
    """Mock holiday checker for testing."""

    def __init__(self, holidays: set[date]):
        """Initialize with a set of holiday dates."""
        self.holidays = holidays

    def is_holiday(self, check_date: date) -> bool:
        """Check if a date is a holiday."""
        return check_date in self.holidays


class TestWeekdayOnlyStrategy(unittest.TestCase):
    """Test cases for WeekdayOnlyStrategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = WeekdayOnlyStrategy()

    def test_distributes_hours_across_weekdays_only(self):
        """Test that hours are distributed only across weekdays."""
        # Task scheduled Friday to Tuesday (5 days, 3 weekdays)
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),  # Friday
            planned_end=datetime(2025, 1, 14, 18, 0, 0),  # Tuesday
            estimated_duration=6.0,
        )

        result = self.strategy.compute_from_planned_period(task)

        # Should have entries for Friday (10th), Monday (13th), Tuesday (14th)
        # 6 hours / 3 weekdays = 2 hours per day
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[task.planned_start.date()], 2.0)  # Friday
        self.assertAlmostEqual(result[datetime(2025, 1, 13).date()], 2.0)  # Monday
        self.assertAlmostEqual(result[task.planned_end.date()], 2.0)  # Tuesday

        # Weekend should NOT be in result
        self.assertNotIn(datetime(2025, 1, 11).date(), result)  # Saturday
        self.assertNotIn(datetime(2025, 1, 12).date(), result)  # Sunday

    def test_returns_empty_dict_for_weekend_only_task(self):
        """Test that weekend-only tasks return empty dict."""
        # Task scheduled Saturday to Sunday only
        task = Task(
            id=1,
            name="Weekend Task",
            priority=1,
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 12, 18, 0, 0),  # Sunday
            estimated_duration=10.0,
        )

        result = self.strategy.compute_from_planned_period(task)

        # Should return empty dict (no weekdays in period)
        self.assertEqual(result, {})

    def test_returns_empty_dict_for_missing_fields(self):
        """Test that tasks with missing fields return empty dict."""
        # No planned_start
        task1 = Task(
            id=1,
            name="No Start",
            priority=1,
            planned_end=datetime(2025, 1, 14, 18, 0, 0),
            estimated_duration=6.0,
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task1), {})

        # No planned_end
        task2 = Task(
            id=2,
            name="No End",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),
            estimated_duration=6.0,
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task2), {})

        # No estimated_duration
        task3 = Task(
            id=3,
            name="No Duration",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),
            planned_end=datetime(2025, 1, 14, 18, 0, 0),
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task3), {})


class TestActualScheduleStrategy(unittest.TestCase):
    """Test cases for ActualScheduleStrategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ActualScheduleStrategy()

    def test_distributes_hours_across_weekdays_in_period(self):
        """Test that hours are distributed across weekdays within the scheduled period."""
        # Task scheduled Friday to Tuesday (5 days total, 3 weekdays)
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),  # Friday
            planned_end=datetime(2025, 1, 14, 18, 0, 0),  # Tuesday
            estimated_duration=10.0,
        )

        result = self.strategy.compute_from_planned_period(task)

        # Should have entries for 3 weekdays only (Fri, Mon, Tue)
        # 10 hours / 3 weekdays = 3.33 hours per day
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(
            result[datetime(2025, 1, 10).date()], 3.33, places=2
        )  # Friday
        self.assertAlmostEqual(
            result[datetime(2025, 1, 13).date()], 3.33, places=2
        )  # Monday
        self.assertAlmostEqual(
            result[datetime(2025, 1, 14).date()], 3.33, places=2
        )  # Tuesday

        # Weekend should NOT be in result
        self.assertNotIn(datetime(2025, 1, 11).date(), result)  # Saturday
        self.assertNotIn(datetime(2025, 1, 12).date(), result)  # Sunday

    def test_handles_weekend_only_task(self):
        """Test that weekend-only tasks are properly calculated."""
        # Task scheduled Saturday to Sunday only
        task = Task(
            id=1,
            name="Weekend Task",
            priority=1,
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 12, 18, 0, 0),  # Sunday
            estimated_duration=10.0,
        )

        result = self.strategy.compute_from_planned_period(task)

        # Should have entries for both weekend days
        # 10 hours / 2 days = 5 hours per day
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[datetime(2025, 1, 11).date()], 5.0)  # Saturday
        self.assertAlmostEqual(result[datetime(2025, 1, 12).date()], 5.0)  # Sunday

    def test_single_day_task(self):
        """Test that single-day tasks work correctly."""
        # Task scheduled for one day only
        task = Task(
            id=1,
            name="Single Day Task",
            priority=1,
            planned_start=datetime(2025, 1, 11, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 1, 11, 18, 0, 0),  # Same Saturday
            estimated_duration=8.0,
        )

        result = self.strategy.compute_from_planned_period(task)

        # Should have entry for one day with all hours
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[datetime(2025, 1, 11).date()], 8.0)

    def test_returns_empty_dict_for_missing_fields(self):
        """Test that tasks with missing fields return empty dict."""
        # No planned_start
        task1 = Task(
            id=1,
            name="No Start",
            priority=1,
            planned_end=datetime(2025, 1, 14, 18, 0, 0),
            estimated_duration=6.0,
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task1), {})

        # No planned_end
        task2 = Task(
            id=2,
            name="No End",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),
            estimated_duration=6.0,
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task2), {})

        # No estimated_duration
        task3 = Task(
            id=3,
            name="No Duration",
            priority=1,
            planned_start=datetime(2025, 1, 10, 9, 0, 0),
            planned_end=datetime(2025, 1, 14, 18, 0, 0),
        )
        self.assertEqual(self.strategy.compute_from_planned_period(task3), {})

    def test_excludes_holidays_when_holiday_checker_provided(self):
        """Test that holidays are excluded when holiday checker is provided."""
        # Monday to Wednesday (Jan 6-8, 2025), with Tuesday as a holiday
        holidays = {date(2025, 1, 7)}  # Tuesday is a holiday
        strategy = ActualScheduleStrategy(MockHolidayChecker(holidays))

        task = Task(
            id=1,
            name="Task with Holiday",
            priority=1,
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        result = strategy.compute_from_planned_period(task)

        # Should distribute across working days only (Mon, Wed)
        # 6h / 2 working days = 3h per day
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[date(2025, 1, 6)], 3.0)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 8)], 3.0)  # Wednesday

        # Tuesday (holiday) should NOT be in result
        self.assertNotIn(date(2025, 1, 7), result)

    def test_distributes_across_all_days_when_only_holidays_in_period(self):
        """Test that hours are distributed across all days if period is only holidays."""
        # All days in the period are holidays
        holidays = {
            date(2025, 1, 6),  # Monday
            date(2025, 1, 7),  # Tuesday
            date(2025, 1, 8),  # Wednesday
        }
        strategy = ActualScheduleStrategy(MockHolidayChecker(holidays))

        task = Task(
            id=1,
            name="Holiday-only Task",
            priority=1,
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday (holiday)
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday (holiday)
            estimated_duration=9.0,
        )

        result = strategy.compute_from_planned_period(task)

        # No working days, so distribute across all days
        # 9h / 3 days = 3h per day
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[date(2025, 1, 6)], 3.0)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 7)], 3.0)  # Tuesday
        self.assertAlmostEqual(result[date(2025, 1, 8)], 3.0)  # Wednesday


if __name__ == "__main__":
    unittest.main()
