"""Tests for application layer date helper functions."""

from datetime import date, datetime

from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.infrastructure.holiday_checker import HolidayChecker


class TestIsWorkday:
    """Test cases for is_workday function."""

    def test_workday_without_holiday_checker_weekday(self):
        """Test that weekdays are workdays without holiday checker."""
        monday = date(2025, 1, 6)  # Monday
        assert is_workday(monday) is True

    def test_workday_without_holiday_checker_weekend(self):
        """Test that weekends are not workdays without holiday checker."""
        saturday = date(2025, 1, 4)  # Saturday
        assert is_workday(saturday) is False

    def test_workday_with_holiday_checker_regular_weekday(self):
        """Test that regular weekdays are workdays with holiday checker."""
        checker = HolidayChecker("JP")
        tuesday = date(2025, 1, 7)  # Tuesday, not a holiday
        assert is_workday(tuesday, checker) is True

    def test_workday_with_holiday_checker_holiday(self):
        """Test that holidays are not workdays with holiday checker."""
        checker = HolidayChecker("JP")
        new_year = date(2025, 1, 1)  # New Year's Day
        assert is_workday(new_year, checker) is False

    def test_workday_with_holiday_checker_weekend(self):
        """Test that weekends are not workdays even with holiday checker."""
        checker = HolidayChecker("JP")
        saturday = date(2025, 1, 4)  # Saturday
        assert is_workday(saturday, checker) is False

    def test_workday_with_datetime(self):
        """Test that is_workday works with datetime objects."""
        monday_dt = datetime(2025, 1, 6, 10, 30)  # Monday 10:30
        saturday_dt = datetime(2025, 1, 4, 15, 45)  # Saturday 15:45

        assert is_workday(monday_dt) is True
        assert is_workday(saturday_dt) is False

    def test_workday_golden_week(self):
        """Test that Golden Week holidays are not workdays."""
        checker = HolidayChecker("JP")
        showa_day = date(2025, 4, 29)  # Showa Day
        constitution_day = date(2025, 5, 3)  # Constitution Day

        assert is_workday(showa_day, checker) is False
        assert is_workday(constitution_day, checker) is False
