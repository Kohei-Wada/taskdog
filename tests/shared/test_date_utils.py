"""Tests for date utility functions."""

import unittest
from datetime import date, datetime

from infrastructure.holiday_checker import HolidayChecker
from shared.utils.date_utils import (
    calculate_next_workday,
    get_previous_monday,
    is_weekday,
    is_weekend,
    is_workday,
)


class TestDateUtils(unittest.TestCase):
    """Test cases for date utility functions."""

    def test_calculate_next_workday_monday(self):
        """Test calculation for Monday (should return same day)."""
        monday = datetime(2025, 1, 6)  # Monday
        result = calculate_next_workday(monday)
        self.assertEqual(result.weekday(), 0)  # Monday
        self.assertEqual(result.date(), monday.date())

    def test_calculate_next_workday_friday(self):
        """Test calculation for Friday (should return same day)."""
        friday = datetime(2025, 1, 10)  # Friday
        result = calculate_next_workday(friday)
        self.assertEqual(result.weekday(), 4)  # Friday
        self.assertEqual(result.date(), friday.date())

    def test_calculate_next_workday_saturday(self):
        """Test calculation for Saturday (should return next Monday)."""
        saturday = datetime(2025, 1, 4)  # Saturday
        result = calculate_next_workday(saturday)
        self.assertEqual(result.weekday(), 0)  # Monday
        self.assertEqual(result.date(), datetime(2025, 1, 6).date())  # Next Monday

    def test_calculate_next_workday_sunday(self):
        """Test calculation for Sunday (should return next Monday)."""
        sunday = datetime(2025, 1, 5)  # Sunday
        result = calculate_next_workday(sunday)
        self.assertEqual(result.weekday(), 0)  # Monday
        self.assertEqual(result.date(), datetime(2025, 1, 6).date())  # Next Monday


class TestGetPreviousMonday(unittest.TestCase):
    """Test cases for get_previous_monday function."""

    def test_get_previous_monday_on_monday(self):
        """Test that Monday returns itself."""
        monday = date(2025, 1, 6)  # Monday
        result = get_previous_monday(monday)
        self.assertEqual(result, monday)
        self.assertEqual(result.weekday(), 0)  # Monday

    def test_get_previous_monday_on_tuesday(self):
        """Test that Tuesday returns previous Monday."""
        tuesday = date(2025, 1, 7)  # Tuesday
        result = get_previous_monday(tuesday)
        self.assertEqual(result, date(2025, 1, 6))  # Previous Monday
        self.assertEqual(result.weekday(), 0)  # Monday

    def test_get_previous_monday_on_wednesday(self):
        """Test that Wednesday returns previous Monday."""
        wednesday = date(2025, 1, 8)  # Wednesday
        result = get_previous_monday(wednesday)
        self.assertEqual(result, date(2025, 1, 6))  # Monday of this week
        self.assertEqual(result.weekday(), 0)  # Monday

    def test_get_previous_monday_on_sunday(self):
        """Test that Sunday returns previous Monday (6 days ago)."""
        sunday = date(2025, 1, 12)  # Sunday
        result = get_previous_monday(sunday)
        self.assertEqual(result, date(2025, 1, 6))  # Monday of this week
        self.assertEqual(result.weekday(), 0)  # Monday

    def test_get_previous_monday_default_none(self):
        """Test that None uses today's date."""
        result = get_previous_monday(None)
        # Should return a Monday
        self.assertEqual(result.weekday(), 0)
        # Should be <= today
        self.assertLessEqual(result, date.today())

    def test_get_previous_monday_no_argument(self):
        """Test that no argument uses today's date."""
        result = get_previous_monday()
        # Should return a Monday
        self.assertEqual(result.weekday(), 0)
        # Should be <= today
        self.assertLessEqual(result, date.today())


class TestWeekdayHelpers(unittest.TestCase):
    """Test cases for is_weekday and is_weekend helper functions."""

    def test_is_weekday_monday(self):
        """Test that Monday is a weekday."""
        monday = date(2025, 1, 6)  # Monday
        self.assertTrue(is_weekday(monday))
        self.assertFalse(is_weekend(monday))

    def test_is_weekday_friday(self):
        """Test that Friday is a weekday."""
        friday = date(2025, 1, 10)  # Friday
        self.assertTrue(is_weekday(friday))
        self.assertFalse(is_weekend(friday))

    def test_is_weekend_saturday(self):
        """Test that Saturday is a weekend."""
        saturday = date(2025, 1, 4)  # Saturday
        self.assertFalse(is_weekday(saturday))
        self.assertTrue(is_weekend(saturday))

    def test_is_weekend_sunday(self):
        """Test that Sunday is a weekend."""
        sunday = date(2025, 1, 5)  # Sunday
        self.assertFalse(is_weekday(sunday))
        self.assertTrue(is_weekend(sunday))

    def test_is_weekday_with_datetime(self):
        """Test that helper functions work with datetime objects."""
        monday_dt = datetime(2025, 1, 6, 10, 30)  # Monday 10:30
        saturday_dt = datetime(2025, 1, 4, 15, 45)  # Saturday 15:45

        self.assertTrue(is_weekday(monday_dt))
        self.assertFalse(is_weekend(monday_dt))
        self.assertFalse(is_weekday(saturday_dt))
        self.assertTrue(is_weekend(saturday_dt))


class TestIsWorkday(unittest.TestCase):
    """Test cases for is_workday function."""

    def test_workday_without_holiday_checker_weekday(self):
        """Test that weekdays are workdays without holiday checker."""
        monday = date(2025, 1, 6)  # Monday
        self.assertTrue(is_workday(monday))

    def test_workday_without_holiday_checker_weekend(self):
        """Test that weekends are not workdays without holiday checker."""
        saturday = date(2025, 1, 4)  # Saturday
        self.assertFalse(is_workday(saturday))

    def test_workday_with_holiday_checker_regular_weekday(self):
        """Test that regular weekdays are workdays with holiday checker."""
        checker = HolidayChecker("JP")
        tuesday = date(2025, 1, 7)  # Tuesday, not a holiday
        self.assertTrue(is_workday(tuesday, checker))

    def test_workday_with_holiday_checker_holiday(self):
        """Test that holidays are not workdays with holiday checker."""
        checker = HolidayChecker("JP")
        new_year = date(2025, 1, 1)  # New Year's Day
        self.assertFalse(is_workday(new_year, checker))

    def test_workday_with_holiday_checker_weekend(self):
        """Test that weekends are not workdays even with holiday checker."""
        checker = HolidayChecker("JP")
        saturday = date(2025, 1, 4)  # Saturday
        self.assertFalse(is_workday(saturday, checker))

    def test_workday_with_datetime(self):
        """Test that is_workday works with datetime objects."""
        monday_dt = datetime(2025, 1, 6, 10, 30)  # Monday 10:30
        saturday_dt = datetime(2025, 1, 4, 15, 45)  # Saturday 15:45

        self.assertTrue(is_workday(monday_dt))
        self.assertFalse(is_workday(saturday_dt))

    def test_workday_golden_week(self):
        """Test that Golden Week holidays are not workdays."""
        checker = HolidayChecker("JP")
        showa_day = date(2025, 4, 29)  # Showa Day
        constitution_day = date(2025, 5, 3)  # Constitution Day

        self.assertFalse(is_workday(showa_day, checker))
        self.assertFalse(is_workday(constitution_day, checker))


if __name__ == "__main__":
    unittest.main()
