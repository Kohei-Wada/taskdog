"""Tests for date utility functions."""

import unittest
from datetime import date, datetime

from shared.utils.date_utils import calculate_next_workday, get_previous_monday


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


if __name__ == "__main__":
    unittest.main()
