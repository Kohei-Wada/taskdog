"""Tests for date utility functions."""

import unittest
from datetime import datetime

from shared.date_utils import calculate_next_workday


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


if __name__ == "__main__":
    unittest.main()
